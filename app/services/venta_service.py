from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.venta_repository import VentaRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.caja_repository import CajaRepository
from app.models.ventas import MetodoPago
from app.services.inventario_service import InventarioService
from app.schemas.inventario_schema import MovimientoInventarioCreate
from app.repositories.movimiento_caja_repository import MovimientoCajaRepository
from app.models.inventario.tipo_movimiento import TipoMovimiento
from app.models.empresas import CajaSesion


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
            metodo_pago = None
            if payload.id_metodo_pago is not None:
                metodo_pago = (
                    db.query(MetodoPago)
                    .filter(MetodoPago.id_metodo_pago == payload.id_metodo_pago)
                    .first()
                )
                if metodo_pago is None:
                    raise HTTPException(status_code=404, detail="Metodo de pago no encontrado.")

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

            # Crear venta
            venta_datos = {
                "id_tipo_venta": payload.id_tipo_venta,
                "id_cliente": payload.id_cliente,
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

            # Obtener id_tipo_movimiento para "Venta" (reducción de stock)
            tipo_venta: TipoMovimiento | None = (
                db.query(TipoMovimiento).filter(TipoMovimiento.nombre == "Venta").first()
            )
            id_tipo_movimiento_venta = tipo_venta.id_tipo_movimiento if tipo_venta else 3

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
                        )
                except LookupError as le:
                    raise HTTPException(status_code=404, detail=str(le))
                except ValueError as ve:
                    raise HTTPException(status_code=400, detail=str(ve))

            # Crear movimiento de caja asociado a la venta
            movimiento_caja_datos = {
                "id_caja_sesion": id_caja_sesion,
                "id_tipo_movimiento_caja": 2,  # INGRESO (seed default)
                "monto": payload.total,
                "concepto": f"Venta {venta.id_venta}",
                "id_metodo_pago": payload.id_metodo_pago,
                "id_usuario": current_user.id_usuario,
            }
            movimiento_caja = MovimientoCajaRepository.crear_movimiento(db, movimiento_caja_datos)

            venta_pago = None
            if payload.id_metodo_pago is not None:
                venta_pago = VentaRepository.crear_venta_pago(
                    db=db,
                    datos={
                        "id_venta": venta.id_venta,
                        "id_metodo_pago": payload.id_metodo_pago,
                        "monto": payload.total,
                        "fecha": datetime.utcnow(),
                    },
                )

            # Commit transaction una vez todo creado
            db.commit()

            # Recuperar la venta con sus detalles cargados para poder serializarla sin problemas
            venta = VentaRepository.obtener_venta_por_id(db=db, id_venta=venta.id_venta)
            if venta is None:
                raise HTTPException(status_code=500, detail="No se pudo recuperar la venta creada.")

            return {
                "venta": venta,
                "detalles": detalles_creados,
                "movimiento_caja": movimiento_caja,
                "venta_pago": venta_pago,
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
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
