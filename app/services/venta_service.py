from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.repositories.venta_repository import VentaRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.caja_repository import CajaRepository
from app.repositories.cliente_repository import ClienteRepository
from app.models.ventas import MetodoPago, TipoVenta
from app.services.inventario_service import InventarioService
from app.schemas.inventario_schema import MovimientoInventarioCreate
from app.repositories.movimiento_caja_repository import MovimientoCajaRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.models.inventario.tipo_movimiento import TipoMovimiento
from app.models.empresas import CajaSesion, TipoMovimientoCaja
from app.services.factura_service import FacturaService


class VentaService:
    @staticmethod
    def _validar_caja_sesion_del_usuario(caja_sesion: CajaSesion, current_user) -> None:
        if getattr(current_user, "id_usuario", None) is None:
            raise HTTPException(status_code=403, detail="Usuario no valido para esta operacion.")
        if caja_sesion.id_usuario != current_user.id_usuario:
            raise HTTPException(status_code=403, detail="La caja sesion no fue creada por el usuario actual.")

    @staticmethod
    def crear_venta_completa(db: Session, current_user, id_caja_sesion: int, payload) -> dict:
        # Validar caja_sesion
        caja_sesion: CajaSesion | None = CajaRepository.obtener_caja_sesion_por_id(db, id_caja_sesion)
        if not caja_sesion:
            raise HTTPException(status_code=404, detail="Caja sesion no encontrada.")

        VentaService._validar_caja_sesion_del_usuario(caja_sesion=caja_sesion, current_user=current_user)

        # validar pertenencia de la empresa
        if getattr(current_user, "id_empresa", None) is not None and caja_sesion.caja.sucursal.id_empresa != current_user.id_empresa:
            raise HTTPException(status_code=403, detail="La caja sesion no pertenece a la empresa del usuario.")

        try:
            tipo_venta_payload = (
                db.query(TipoVenta)
                .filter(TipoVenta.id_tipo_venta == payload.id_tipo_venta)
                .first()
            )
            if tipo_venta_payload is None:
                raise HTTPException(status_code=404, detail="Tipo de venta no encontrado.")
            es_venta_credito = (tipo_venta_payload.nombre or "").strip().upper() in {"CREDITO", "CRÉDITO"}

            pagos_payload = [
                {"id_metodo_pago": pago.id_metodo_pago, "monto": pago.monto}
                for pago in (payload.pagos or [])
            ]
            if not pagos_payload and payload.id_metodo_pago is not None:
                pagos_payload = [{"id_metodo_pago": payload.id_metodo_pago, "monto": payload.total}]
            if es_venta_credito and pagos_payload:
                raise HTTPException(status_code=400, detail="Una venta a credito no debe enviar pagos ni metodo de pago.")

            ids_metodos_pago = [pago["id_metodo_pago"] for pago in pagos_payload]
            if len(ids_metodos_pago) != len(set(ids_metodos_pago)):
                raise HTTPException(status_code=400, detail="No se puede repetir el mismo metodo de pago en una venta.")

            total_pagado = Decimal("0.00")
            for pago in pagos_payload:
                if pago["id_metodo_pago"] <= 0:
                    raise HTTPException(status_code=400, detail="Metodo de pago invalido.")
                if pago["monto"] <= 0:
                    raise HTTPException(status_code=400, detail="El monto de cada pago debe ser mayor a cero.")

                metodo_pago = (
                    db.query(MetodoPago)
                    .filter(MetodoPago.id_metodo_pago == pago["id_metodo_pago"])
                    .first()
                )
                if metodo_pago is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Metodo de pago {pago['id_metodo_pago']} no encontrado.",
                    )
                total_pagado += pago["monto"]

            if pagos_payload and total_pagado != payload.total:
                raise HTTPException(status_code=400, detail="La suma de los pagos debe ser igual al total de la venta.")

            id_cliente = payload.id_cliente
            cliente = None
            if id_cliente is not None:
                if id_cliente <= 0:
                    raise HTTPException(status_code=400, detail="Cliente invalido. Envie null si la venta no tiene cliente.")
                cliente = ClienteRepository.obtener_cliente_por_id(db=db, id_cliente=id_cliente)
                if cliente is None:
                    raise HTTPException(status_code=404, detail="Cliente no encontrado.")
            if es_venta_credito:
                if cliente is None:
                    raise HTTPException(status_code=400, detail="Una venta a credito debe tener cliente.")
                if cliente.categoria_cliente is None:
                    raise HTTPException(status_code=400, detail="El cliente no tiene categoria asociada para calcular el plazo de credito.")
            if payload.factura_linea and cliente is None:
                raise HTTPException(
                    status_code=400,
                    detail="Para generar factura en linea debe seleccionar un cliente.",
                )

            # Normalizar el estado a los valores permitidos por la DB
            estado_input = getattr(payload, "estado", None)
            map_estado = {
                "PENDIENTE": "PENDIENTE_COBRO",
                "PENDIENTE_COBRO": "PENDIENTE_COBRO",
                "PAGADA": "PAGADA",
                "CREDITO": "CREDITO",
                "ANULADA": "ANULADA",
            }
            estado_norm = None
            if estado_input:
                try:
                    estado_norm = map_estado.get(str(estado_input).strip().upper())
                except Exception:
                    estado_norm = None
            if not estado_norm:
                estado_norm = "PENDIENTE_COBRO"
            if es_venta_credito:
                estado_norm = "CREDITO"
            elif pagos_payload:
                estado_norm = "PAGADA"

            # Crear venta
            venta_datos = {
                "id_tipo_venta": payload.id_tipo_venta,
                "id_cliente": id_cliente,
                "id_caja_sesion": id_caja_sesion,
                "id_usuario": current_user.id_usuario,
                "subtotal": payload.subtotal,
                "descuento_total": payload.descuento_total or Decimal("0.00"),
                "total": payload.total,
                "fecha": datetime.utcnow(),
                "estado": estado_norm,
            }
            venta = VentaRepository.crear_venta(db, venta_datos)

            detalles_creados = []
            detalles_factura = []

            # Obtener id_tipo_movimiento para "Venta" (reducción de stock)
            tipo_venta: TipoMovimiento | None = (
                db.query(TipoMovimiento).filter(TipoMovimiento.nombre == "Venta").first()
            )
            if tipo_venta is None:
                raise HTTPException(
                    status_code=500,
                    detail='Tipo de movimiento de inventario "Venta" no configurado.',
                )
            id_tipo_movimiento_venta = tipo_venta.id_tipo_movimiento

            # Procesar cada detalle: insert detalle + usar InventarioService.crear_movimiento
            for d in payload.detalles:
                # validar producto
                producto = ProductoRepository.obtener_producto_por_id(db, d.id_producto)
                if not producto:
                    raise HTTPException(status_code=404, detail=f"Producto {d.id_producto} no encontrado.")

                detalle_datos = {
                    "id_venta": venta.id_venta,
                    "id_producto": d.id_producto,
                    "cantidad": d.cantidad,
                    "precio_unitario": d.precio_unitario,
                    "descuento": d.descuento or Decimal("0.00"),
                    "subtotal": d.subtotal,
                    "total": d.subtotal,
                    "descripcion": d.descripcion,
                }
                detalle = VentaRepository.crear_detalle(db, detalle_datos)
                detalles_creados.append(detalle)
                detalles_factura.append(
                    {
                        "id_producto": d.id_producto,
                        "producto": producto.nombre,
                        "cantidad": d.cantidad,
                        "subtotal": d.subtotal,
                    }
                )

                # Usar InventarioService para crear movimiento y actualizar stock
                movimiento_payload = MovimientoInventarioCreate(
                    id_producto=d.id_producto,
                    id_tipo_movimiento=id_tipo_movimiento_venta,
                    cantidad=d.cantidad,
                    observacion=f"Movimiento de la venta {venta.id_venta}",
                )
                try:
                        InventarioService.crear_movimiento(
                            db=db,
                            current_user=current_user,
                            id_empresa=caja_sesion.caja.sucursal.id_empresa,
                            id_sucursal=caja_sesion.caja.id_sucursal,
                            payload=movimiento_payload,
                            commit=False,
                        )
                except LookupError as le:
                    raise HTTPException(status_code=404, detail=str(le))
                except ValueError as ve:
                    raise HTTPException(status_code=400, detail=str(ve))

            movimientos_caja = []
            ventas_pago = []
            cuenta_por_cobrar = None
            if es_venta_credito:
                fecha_inicio = datetime.utcnow()
                cuenta_por_cobrar = VentaRepository.crear_cuenta_por_cobrar(
                    db=db,
                    datos={
                        "id_venta": venta.id_venta,
                        "monto_credito": payload.total,
                        "saldo_pendiente": payload.total,
                        "fecha_inicio": fecha_inicio,
                        "fecha_vencimiento": fecha_inicio + timedelta(days=cliente.categoria_cliente.plazo_credito),
                        "estado": "PENDIENTE",
                    },
                )

            for pago in ([] if es_venta_credito else pagos_payload):
                movimiento_caja_datos = {
                    "id_caja_sesion": id_caja_sesion,
                    "id_tipo_movimiento_caja": 2,  # INGRESO (seed default)
                    "monto": pago["monto"],
                    "concepto": f"Venta {venta.id_venta}",
                    "id_metodo_pago": pago["id_metodo_pago"],
                    "id_usuario": current_user.id_usuario,
                }
                movimientos_caja.append(MovimientoCajaRepository.crear_movimiento(db, movimiento_caja_datos))

                ventas_pago.append(VentaRepository.crear_venta_pago(
                    db=db,
                    datos={
                        "id_venta": venta.id_venta,
                        "id_metodo_pago": pago["id_metodo_pago"],
                        "monto": pago["monto"],
                        "fecha": datetime.utcnow(),
                    },
                ))

            factura = None
            ruta_pdf_factura = None
            if payload.factura_linea:
                empresa = caja_sesion.caja.sucursal.empresa
                factura, ruta_pdf_factura = FacturaService.crear_factura(
                    db=db,
                    venta=venta,
                    cliente=cliente,
                    empresa=empresa,
                    detalles=detalles_factura,
                )

            # Commit transaction una vez todo creado
            db.commit()

            # Recuperar la venta con sus detalles cargados para poder serializarla sin problemas
            venta = VentaRepository.obtener_venta_por_id(db=db, id_venta=venta.id_venta)
            if venta is None:
                raise HTTPException(status_code=500, detail="No se pudo recuperar la venta creada.")

            factura_email_enviado = None
            if factura is not None and ruta_pdf_factura is not None:
                db.refresh(factura)
                factura_email_enviado = FacturaService.enviar_factura(
                    cliente=cliente,
                    factura=factura,
                    ruta_pdf=ruta_pdf_factura,
                )

            return {
                "venta": venta,
                "detalles": detalles_creados,
                "movimientos_caja": movimientos_caja,
                "ventas_pago": ventas_pago,
                "cuenta_por_cobrar": cuenta_por_cobrar,
                "factura": factura,
                "factura_email_enviado": factura_email_enviado,
            }

        except HTTPException:
            try:
                db.rollback()
            except OperationalError:
                db.invalidate()
            raise
        except Exception as e:
            try:
                db.rollback()
            except OperationalError:
                db.invalidate()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def obtener_historial_por_caja_sesion(
        db: Session,
        current_user,
        id_caja_sesion: int,
    ) -> list:
        caja_sesion: CajaSesion | None = CajaRepository.obtener_caja_sesion_por_id(db, id_caja_sesion)
        if not caja_sesion:
            raise HTTPException(status_code=404, detail="Caja sesion no encontrada.")

        VentaService._validar_caja_sesion_del_usuario(caja_sesion=caja_sesion, current_user=current_user)

        if getattr(current_user, "id_empresa", None) is not None and caja_sesion.caja.sucursal.id_empresa != current_user.id_empresa:
            raise HTTPException(status_code=403, detail="La caja sesion no pertenece a la empresa del usuario.")

        try:
            return VentaRepository.obtener_ventas_por_caja_sesion(db=db, id_caja_sesion=id_caja_sesion)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def obtener_cuentas_por_cobrar_de_cliente(
        db: Session,
        current_user,
        id_empresa: int,
        id_cliente: int,
    ) -> list:
        usuario_rol = EmpresaRepository.obtener_usuario_rol_activo(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if usuario_rol is None:
            raise LookupError("Empresa no encontrada para este usuario.")

        cliente = ClienteRepository.obtener_cliente_por_id(
            db=db,
            id_cliente=id_cliente,
        )
        if cliente is None:
            raise LookupError("Cliente no encontrado.")

        empresa_del_cliente = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=cliente.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa_del_cliente is None:
            raise LookupError("Cliente no encontrado para esta empresa.")

        rol_operador = EmpresaRepository.obtener_usuario_rol_activo_distinto_cliente(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if rol_operador is None and cliente.id_usuario != current_user.id_usuario:
            raise PermissionError(
                "No tiene permiso para consultar las cuentas por cobrar de este cliente."
            )

        return VentaRepository.obtener_cuentas_por_cobrar_por_empresa_y_cliente(
            db=db,
            id_empresa=id_empresa,
            id_cliente=id_cliente,
        )

    @staticmethod
    def registrar_pago_cuenta_por_cobrar(
        db: Session,
        current_user,
        id_caja_sesion: int,
        payload,
    ) -> dict:
        caja_sesion = CajaRepository.obtener_caja_sesion_por_id(
            db=db,
            id_caja_sesion=id_caja_sesion,
        )
        if caja_sesion is None:
            raise HTTPException(status_code=404, detail="Caja sesion no encontrada.")

        VentaService._validar_caja_sesion_del_usuario(
            caja_sesion=caja_sesion,
            current_user=current_user,
        )
        if caja_sesion.estado != "Abierto":
            raise HTTPException(status_code=400, detail="La caja sesion debe estar abierta.")

        try:
            cuenta = VentaRepository.obtener_cuenta_por_cobrar_para_actualizar(
                db=db,
                id_cxc=payload.id_cxc,
            )
            if cuenta is None:
                raise HTTPException(status_code=404, detail="Cuenta por cobrar no encontrada.")

            id_empresa_sesion = caja_sesion.caja.sucursal.id_empresa
            id_empresa_cuenta = cuenta.venta.caja_sesion.caja.sucursal.id_empresa
            if id_empresa_cuenta != id_empresa_sesion:
                raise HTTPException(
                    status_code=400,
                    detail="La cuenta por cobrar no pertenece a la empresa de la caja sesion.",
                )

            saldo_anterior = Decimal(cuenta.saldo_pendiente or 0)
            if saldo_anterior <= Decimal("0.00") or cuenta.estado == "PAGADA":
                raise HTTPException(
                    status_code=400,
                    detail="La cuenta por cobrar ya se encuentra pagada.",
                )

            pagos_payload = list(payload.pagos_credito)
            ids_metodos = [pago.id_metodo_pago for pago in pagos_payload]
            if len(ids_metodos) != len(set(ids_metodos)):
                raise HTTPException(
                    status_code=400,
                    detail="No se puede repetir el mismo metodo de pago.",
                )

            metodos_pago = {
                metodo.id_metodo_pago: metodo
                for metodo in db.query(MetodoPago)
                .filter(MetodoPago.id_metodo_pago.in_(ids_metodos))
                .all()
            }
            if len(metodos_pago) != len(ids_metodos):
                raise HTTPException(
                    status_code=404,
                    detail="Uno o mas metodos de pago no fueron encontrados.",
                )

            metodos_permitidos = {"EFECTIVO", "QR", "TARJETA"}
            for metodo in metodos_pago.values():
                if (metodo.nombre or "").strip().upper() not in metodos_permitidos:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"El metodo de pago {metodo.nombre} no esta permitido para "
                            "pagos de credito."
                        ),
                    )

            total_pagado = sum(
                (Decimal(pago.monto_pagado) for pago in pagos_payload),
                Decimal("0.00"),
            )
            if total_pagado > saldo_anterior:
                raise HTTPException(
                    status_code=400,
                    detail="El total pagado no puede ser mayor al saldo pendiente.",
                )

            tipo_ingreso = (
                db.query(TipoMovimientoCaja)
                .filter(TipoMovimientoCaja.nombre == "INGRESO")
                .first()
            )
            if tipo_ingreso is None:
                raise HTTPException(
                    status_code=500,
                    detail="Tipo de movimiento de caja INGRESO no configurado.",
                )

            fecha_pago = datetime.utcnow()
            pagos_creados = []
            movimientos_creados = []
            for pago in pagos_payload:
                pago_creado = VentaRepository.crear_pago_credito(
                    db=db,
                    datos={
                        "id_cxc": cuenta.id_cxc,
                        "id_metodo_pago": pago.id_metodo_pago,
                        "monto_pagado": pago.monto_pagado,
                        "fecha_pago": fecha_pago,
                    },
                )
                pagos_creados.append(pago_creado)

                movimiento = MovimientoCajaRepository.crear_movimiento(
                    db=db,
                    datos={
                        "id_metodo_pago": pago.id_metodo_pago,
                        "id_tipo_movimiento_caja": tipo_ingreso.id_tipo_movimiento_caja,
                        "id_caja_sesion": id_caja_sesion,
                        "id_usuario": current_user.id_usuario,
                        "fecha": fecha_pago,
                        "monto": pago.monto_pagado,
                        "concepto": f"PAGO_CREDITO CXC {cuenta.id_cxc}",
                    },
                )
                movimientos_creados.append(movimiento)

            cuenta.saldo_pendiente = saldo_anterior - total_pagado
            if cuenta.saldo_pendiente == Decimal("0.00"):
                cuenta.estado = "PAGADA"
            elif cuenta.estado == "PAGADA":
                cuenta.estado = "PENDIENTE"

            db.commit()
            db.refresh(cuenta)
            for pago in pagos_creados:
                db.refresh(pago)
            for movimiento in movimientos_creados:
                db.refresh(movimiento)

            # --- NOTIFICACIÓN PUSH REAL ---
            try:
                import traceback
                print("[TRACE COBRO] inicio", flush=True)
                print("[TRACE COBRO] pago confirmado", flush=True)
                id_empresa_cuenta = cuenta.venta.caja_sesion.caja.sucursal.id_empresa
                print(f"[TRACE COBRO] id_empresa_cuenta={id_empresa_cuenta}", flush=True)
                
                client_user_id = None
                if cuenta.venta and cuenta.venta.cliente:
                    client_user_id = cuenta.venta.cliente.id_usuario
                print(f"[TRACE COBRO] client_user_id={client_user_id}", flush=True)

                if client_user_id:
                    from app.services.notification_service import NotificationService
                    notification_payload = {
                        "id_cxc": str(cuenta.id_cxc),
                        "id_empresa": str(id_empresa_cuenta),
                        "id_usuario": str(client_user_id),
                        "monto_pagado": str(total_pagado),
                        "saldo_pendiente": str(cuenta.saldo_pendiente),
                        "estado": cuenta.estado
                    }
                    print("[TRACE COBRO] antes enviar_notificacion_usuario", flush=True)
                    resultado_fcm = NotificationService.enviar_notificacion_usuario(
                        db=db,
                        id_usuario=client_user_id,
                        id_empresa=id_empresa_cuenta,
                        titulo="Abono de Crédito Registrado",
                        mensaje=f"Se ha registrado un abono de {total_pagado} a tu crédito. Saldo pendiente: {cuenta.saldo_pendiente}.",
                        payload=notification_payload
                    )
                    print(f"[TRACE COBRO] resultado_fcm={resultado_fcm}", flush=True)
                else:
                    print("[TRACE COBRO] client_user_id es nulo/falso — no se envía push", flush=True)
            except Exception as notif_err:
                print(f"[TRACE COBRO] EXCEPCION en bloque de notificacion: {notif_err}", flush=True)
                traceback.print_exc()

            return {
                "id_cxc": cuenta.id_cxc,
                "id_caja_sesion": id_caja_sesion,
                "monto_credito": cuenta.monto_credito,
                "saldo_anterior": saldo_anterior,
                "total_pagado": total_pagado,
                "saldo_pendiente": cuenta.saldo_pendiente,
                "estado": cuenta.estado,
                "pagos_credito": pagos_creados,
                "movimientos_caja": movimientos_creados,
            }
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(exc)) from exc
