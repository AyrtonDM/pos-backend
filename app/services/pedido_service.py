from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.usuarios import Usuario
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.sucursal_repository import SucursalRepository
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.pedido_schema import (
    PedidoClienteCreate,
    PedidoClienteEstadoUpdate,
    PedidoClienteResponse,
)
from app.services.sucursal_service import SucursalService


class PedidoService:
    ESTADOS_TERMINALES = frozenset({"convertido_en_venta", "entregado", "rechazado", "cancelado"})

    @staticmethod
    def _validar_estados(estado_actual: str, estado_nuevo: str):
        transiciones = {
            "enviado": ["en_revision", "cancelado"],
            "en_revision": ["confirmado", "rechazado", "cancelado"],
            "confirmado": ["en_preparacion"],
            "en_preparacion": ["listo_para_recoger"],
            "listo_para_recoger": ["convertido_en_venta"],
            "convertido_en_venta": ["entregado"],
        }
        if estado_nuevo not in transiciones.get(estado_actual, []):
            raise ValueError(f"Transicion de estado no valida de '{estado_actual}' a '{estado_nuevo}'.")

    @staticmethod
    def _validar_acceso_sucursal(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ) -> None:
        """Verifica que el usuario tenga acceso a la empresa y sucursal del pedido."""
        SucursalService._validar_empresa_del_usuario(db=db, current_user=current_user, id_empresa=id_empresa)
        sucursal = SucursalRepository.obtener_sucursal_por_id(db, id_sucursal)
        if not sucursal or sucursal.id_empresa != id_empresa:
            raise LookupError("Sucursal no encontrada o no pertenece a la empresa.")

    @staticmethod
    def _validar_permiso(db: Session, current_user: Usuario, id_empresa: int, codigo_permiso: str) -> None:
        if current_user is None or not current_user.activo:
            raise PermissionError("Usuario inactivo o no autenticado.")
        
        from app.models.usuarios.rol_permiso import RolPermiso
        from app.models.usuarios.permiso import Permiso
        from app.models.usuarios.usuario_rol import UsuarioRol
        
        # Buscar un rol activo para el usuario en esta empresa
        usuario_roles = (
            db.query(UsuarioRol)
            .filter(
                UsuarioRol.id_usuario == current_user.id_usuario,
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.activo == True
            )
            .all()
        )
        
        if not usuario_roles:
            raise PermissionError("El usuario no tiene un rol activo asignado en esta empresa.")
            
        # Comprobar si alguno de los roles activos del usuario tiene el permiso activo
        for ur in usuario_roles:
            has_perm = (
                db.query(RolPermiso)
                .join(Permiso)
                .filter(
                    RolPermiso.id_rol == ur.id_rol,
                    RolPermiso.activo == True,
                    Permiso.codigo == codigo_permiso
                )
                .first()
            )
            if has_perm:
                return  # Permiso concedido
                
        raise PermissionError(f"No tienes el permiso '{codigo_permiso}' requerido para esta accion.")


    @staticmethod
    def crear_pedido(
        db: Session, current_user: Usuario, id_empresa: int, payload: PedidoClienteCreate
    ) -> PedidoClienteResponse:
        SucursalService._validar_empresa_del_usuario(
            db=db, current_user=current_user, id_empresa=id_empresa
        )

        sucursal = SucursalRepository.obtener_sucursal_por_id(db, payload.id_sucursal)
        if not sucursal or sucursal.id_empresa != id_empresa:
            raise ValueError("Sucursal no encontrada o no pertenece a la empresa.")

        cliente = ClienteRepository.obtener_cliente_por_usuario(db, current_user.id_usuario)
        if not cliente:
            raise ValueError("No se encontró perfil de cliente para este usuario.")

        subtotal = Decimal("0.00")
        descuento = Decimal("0.00")
        
        # Opcional: aplicar logica de CategoriaCliente aquí para descuentos base
        descuento_base_percent = Decimal("0.00")
        if cliente.categoria_cliente:
            descuento_base_percent = Decimal(str(cliente.categoria_cliente.descuento_base)) / Decimal("100")

        try:
            pedido = PedidoRepository.crear_pedido(
                db=db,
                datos={
                    "id_empresa": id_empresa,
                    "id_sucursal": payload.id_sucursal,
                    "id_cliente": cliente.id_cliente,
                    "observacion_cliente": payload.observacion_cliente,
                },
            )

            db.flush()

            for item in payload.detalles:
                producto = ProductoRepository.obtener_producto_por_id(db, item.id_producto)
                if not producto or producto.id_empresa != id_empresa or not producto.activo:
                    raise ValueError(f"Producto {item.id_producto} no es valido o no esta activo.")

                if item.cantidad <= 0:
                    raise ValueError(f"Cantidad para producto {item.id_producto} debe ser mayor a 0.")

                # Verificar stock actual en la sucursal solicitada
                stock_disponible = InventarioRepository.obtener_stock_por_producto_y_sucursal(
                    db, item.id_producto, payload.id_sucursal
                )
                cantidad_stock = stock_disponible.cantidad if stock_disponible else 0
                if item.cantidad > cantidad_stock:
                    raise ValueError({
                        "codigo": "STOCK_INSUFICIENTE",
                        "producto_id": item.id_producto,
                        "producto": producto.nombre,
                        "solicitado": item.cantidad,
                        "disponible": cantidad_stock,
                    })

                precio_real = producto.precio
                subtotal_item = precio_real * item.cantidad
                desc_item = subtotal_item * descuento_base_percent

                PedidoRepository.crear_detalle_pedido(
                    db=db,
                    datos={
                        "id_pedido": pedido.id_pedido,
                        "id_producto": item.id_producto,
                        "cantidad": item.cantidad,
                        "precio_unitario_estimado": precio_real,
                        "descuento_estimado": desc_item,
                        "subtotal_estimado": subtotal_item - desc_item,
                    },
                )
                
                subtotal += subtotal_item
                descuento += desc_item

            pedido = PedidoRepository.actualizar_pedido(
                db=db,
                pedido=pedido,
                datos={
                    "subtotal_estimado": subtotal,
                    "descuento_estimado": descuento,
                    "total_estimado": subtotal - descuento,
                },
            )

            db.commit()
            db.refresh(pedido)
            return PedidoClienteResponse.model_validate(pedido)
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Error de integridad al crear el pedido.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def obtener_pedidos_cliente(
        db: Session, current_user: Usuario
    ) -> list[PedidoClienteResponse]:
        cliente = ClienteRepository.obtener_cliente_por_usuario(db, current_user.id_usuario)
        if not cliente:
            return []
        
        pedidos = PedidoRepository.obtener_pedidos_por_cliente(db, cliente.id_cliente)
        return [PedidoClienteResponse.model_validate(p) for p in pedidos]

    @staticmethod

    def obtener_pedidos_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: Optional[int] = None,
        estado: Optional[str] = None,
    ) -> list[PedidoClienteResponse]:
        PedidoService._validar_permiso(db, current_user, id_empresa, "PEDIDO_VER")
        SucursalService._validar_empresa_del_usuario(
            db=db, current_user=current_user, id_empresa=id_empresa
        )
        pedidos = PedidoRepository.obtener_pedidos_por_empresa(
            db, id_empresa, id_sucursal=id_sucursal, estado=estado
        )
        return [PedidoClienteResponse.model_validate(p) for p in pedidos]

    @staticmethod
    def obtener_pedido_propio(
        db: Session, current_user: Usuario, id_pedido: int
    ) -> PedidoClienteResponse:
        """Para Flutter: el cliente consulta uno de sus propios pedidos."""
        cliente = ClienteRepository.obtener_cliente_por_usuario(db, current_user.id_usuario)
        if not cliente:
            raise LookupError("No se encontro perfil de cliente.")
        pedido = PedidoRepository.obtener_pedido_por_id(db, id_pedido)
        if not pedido or pedido.id_cliente != cliente.id_cliente:
            raise LookupError("Pedido no encontrado o no pertenece a este cliente.")
        return PedidoClienteResponse.model_validate(pedido)

    @staticmethod
    def obtener_pedido_empresa(
        db: Session, current_user: Usuario, id_empresa: int, id_pedido: int
    ) -> PedidoClienteResponse:
        """Para Angular: cajero/admin consulta detalle de un pedido de su empresa."""
        PedidoService._validar_permiso(db, current_user, id_empresa, "PEDIDO_VER")
        SucursalService._validar_empresa_del_usuario(
            db=db, current_user=current_user, id_empresa=id_empresa
        )
        pedido = PedidoRepository.obtener_pedido_por_id(db, id_pedido)
        if not pedido or pedido.id_empresa != id_empresa:
            raise LookupError("Pedido no encontrado.")
        return PedidoClienteResponse.model_validate(pedido)

    @staticmethod
    def cancelar_pedido_cliente(
        db: Session, current_user: Usuario, id_pedido: int
    ) -> PedidoClienteResponse:
        cliente = ClienteRepository.obtener_cliente_por_usuario(db, current_user.id_usuario)
        if not cliente:
            raise ValueError("No se encontró perfil de cliente.")

        pedido = PedidoRepository.obtener_pedido_por_id(db, id_pedido)
        if not pedido or pedido.id_cliente != cliente.id_cliente:
            raise LookupError("Pedido no encontrado o no pertenece a este cliente.")

        PedidoService._validar_estados(pedido.estado, "cancelado")

        try:
            pedido = PedidoRepository.actualizar_pedido(
                db=db,
                pedido=pedido,
                datos={
                    "estado": "cancelado",
                    "fecha_cancelacion": datetime.utcnow(),
                },
            )
            db.commit()
            db.refresh(pedido)
            return PedidoClienteResponse.model_validate(pedido)
        except Exception as exc:
            db.rollback()
            raise ValueError("No se pudo cancelar el pedido.") from exc

    @staticmethod
    def actualizar_estado_pedido(
        db: Session, current_user: Usuario, id_empresa: int, id_pedido: int, payload: PedidoClienteEstadoUpdate
    ) -> PedidoClienteResponse:
        PedidoService._validar_permiso(db, current_user, id_empresa, "PEDIDO_GESTIONAR")
        SucursalService._validar_empresa_del_usuario(
            db=db, current_user=current_user, id_empresa=id_empresa
        )


        pedido = PedidoRepository.obtener_pedido_por_id(db, id_pedido)
        if not pedido or pedido.id_empresa != id_empresa:
            raise LookupError("Pedido no encontrado.")

        # Bloquear conversiones dobles
        if payload.estado == "convertido_en_venta" and pedido.id_venta is not None:
            raise ValueError("El pedido ya fue convertido en venta.")

        PedidoService._validar_estados(pedido.estado, payload.estado)

        datos_actualizar = {"estado": payload.estado}

        if payload.observacion_empresa:
            datos_actualizar["observacion_empresa"] = payload.observacion_empresa

        fecha_actual = datetime.utcnow()
        if payload.estado == "confirmado":
            datos_actualizar["fecha_confirmacion"] = fecha_actual
        elif payload.estado == "en_preparacion":
            datos_actualizar["fecha_preparacion"] = fecha_actual
        elif payload.estado == "listo_para_recoger":
            datos_actualizar["fecha_listo"] = fecha_actual
        elif payload.estado in ["cancelado", "rechazado"]:
            datos_actualizar["fecha_cancelacion"] = fecha_actual

        try:
            pedido = PedidoRepository.actualizar_pedido(
                db=db,
                pedido=pedido,
                datos=datos_actualizar,
            )
            db.commit()
            db.refresh(pedido)

            # Notificar al cliente via FCM (no-bloqueo: un error FCM no revierte el cambio)
            try:
                from app.services.notification_service import NotificationService
                NotificationService.notificar_cambio_estado_pedido(
                    db=db,
                    pedido=pedido,
                    estado_nuevo=payload.estado,
                )
            except Exception:
                pass  # FCM opcional - no revertir el estado

            return PedidoClienteResponse.model_validate(pedido)
        except Exception as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar el estado del pedido.") from exc
