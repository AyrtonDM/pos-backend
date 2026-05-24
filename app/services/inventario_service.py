from datetime import datetime

from app.models.usuarios import Usuario
from sqlalchemy.orm import Session

from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.sucursal_repository import SucursalRepository
from app.schemas.inventario_schema import (
    MovimientoInventarioCreate,
    MovimientoInventarioResponse,
    StockProductoResponse,
    StockUpdateRequest,
    TipoMovimientoResponse,
)
from app.services.notification_service import NotificationService


class InventarioService:
    @staticmethod
    def _validar_usuario_activo(current_user: Usuario) -> None:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

    @staticmethod
    def _validar_empresa_y_sucursal_del_usuario(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ) -> None:
        InventarioService._validar_usuario_activo(current_user)
        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

        sucursal = SucursalRepository.obtener_sucursal_por_empresa(
            db=db,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
        if sucursal is None:
            raise LookupError("Sucursal no encontrada para esta empresa.")

    @staticmethod
    def _serializar_movimiento(movimiento, stock_actual: int) -> dict:
        return {
            "id_movimiento": movimiento.id_movimiento_inventario,
            "id_movimiento_inventario": movimiento.id_movimiento_inventario,
            "id_producto": movimiento.id_producto,
            "id_tipo_movimiento": movimiento.id_tipo_movimiento,
            "id_usuario": movimiento.id_usuario,
            "id_sucursal": movimiento.id_sucursal,
            "cantidad": movimiento.cantidad,
            "observacion": movimiento.observacion,
            "fecha_movimiento": movimiento.fecha_movimiento,
            "stock_actual": stock_actual,
            "producto": movimiento.producto,
            "tipo_movimiento": movimiento.tipo_movimiento,
        }

    @staticmethod
    def _serializar_stock(stock) -> dict:
        return {
            "id_stock": stock.id_stock,
            "id_producto": stock.id_producto,
            "id_sucursal": stock.id_sucursal,
            "cantidad": stock.cantidad,
            "stock_minimo": stock.stock_minimo,
            "stock_maximo": stock.stock_maximo,
            "fecha_actualizacion": stock.fecha_actualizacion,
            "nombre_producto": stock.producto.nombre if stock.producto else "",
            "unidad_medida": stock.producto.unidad_medida if stock.producto else "",
            "precio": float(stock.producto.precio) if stock.producto and stock.producto.precio is not None else 0,
            "imagen": stock.producto.imagen if stock.producto else None,
            "activo": stock.producto.activo if stock.producto else False,
        }

    @staticmethod
    def listar_tipos_movimiento(db: Session) -> list[TipoMovimientoResponse]:
        tipos = InventarioRepository.obtener_tipos_movimiento(db)
        return [TipoMovimientoResponse.model_validate(tipo) for tipo in tipos]

    @staticmethod
    def listar_stock_por_sucursal(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ) -> list[StockProductoResponse]:
        InventarioService._validar_empresa_y_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
        stocks = InventarioRepository.obtener_stocks_por_sucursal(
            db=db,
            id_sucursal=id_sucursal,
        )
        return [
            StockProductoResponse.model_validate(InventarioService._serializar_stock(stock))
            for stock in stocks
            if stock.producto is not None and stock.producto.id_empresa == id_empresa
        ]

    @staticmethod
    def listar_movimientos_por_sucursal(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ) -> list[MovimientoInventarioResponse]:
        InventarioService._validar_empresa_y_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
        movimientos = InventarioRepository.obtener_movimientos_por_sucursal(
            db=db,
            id_sucursal=id_sucursal,
        )
        return [
            MovimientoInventarioResponse.model_validate(
                InventarioService._serializar_movimiento(
                    movimiento=movimiento,
                    stock_actual=0,
                )
            )
            for movimiento in movimientos
            if movimiento.producto is not None and movimiento.producto.id_empresa == id_empresa
        ]

    @staticmethod
    def actualizar_stock_sucursal(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        id_producto: int,
        payload: StockUpdateRequest,
    ) -> StockProductoResponse:
        InventarioService._validar_empresa_y_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )

        if payload.stock_minimo is None and payload.stock_maximo is None:
            raise ValueError("Debe enviar stock_minimo o stock_maximo para actualizar.")
        if payload.stock_minimo is not None and payload.stock_minimo < 0:
            raise ValueError("El stock minimo no puede ser negativo.")
        if payload.stock_maximo is not None and payload.stock_maximo < 0:
            raise ValueError("El stock maximo no puede ser negativo.")

        stock = InventarioRepository.obtener_stock_por_producto_y_sucursal_con_producto(
            db=db,
            id_producto=id_producto,
            id_sucursal=id_sucursal,
        )
        if stock is None:
            raise LookupError("Stock no encontrado para el producto y sucursal indicados.")
        if stock.producto is None or stock.producto.id_empresa != id_empresa:
            raise ValueError("El producto no pertenece a la empresa indicada.")

        nuevo_stock_minimo = payload.stock_minimo if payload.stock_minimo is not None else stock.stock_minimo
        nuevo_stock_maximo = payload.stock_maximo if payload.stock_maximo is not None else stock.stock_maximo

        if (
            nuevo_stock_minimo is not None
            and nuevo_stock_maximo is not None
            and nuevo_stock_minimo > nuevo_stock_maximo
        ):
            raise ValueError("El stock minimo no puede ser mayor al stock maximo.")

        try:
            stock = InventarioRepository.actualizar_stock(
                stock=stock,
                datos={
                    "stock_minimo": nuevo_stock_minimo,
                    "stock_maximo": nuevo_stock_maximo,
                    "fecha_actualizacion": datetime.now(),
                },
                db=db,
            )
            db.commit()
            stock = InventarioRepository.obtener_stock_por_producto_y_sucursal_con_producto(
                db=db,
                id_producto=id_producto,
                id_sucursal=id_sucursal,
            )
            if stock is None:
                raise LookupError("No se pudo recuperar el stock actualizado.")
            return StockProductoResponse.model_validate(
                InventarioService._serializar_stock(stock)
            )
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def crear_movimiento(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        payload: MovimientoInventarioCreate,
    ) -> MovimientoInventarioResponse:
        InventarioService._validar_empresa_y_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )

        producto = ProductoRepository.obtener_producto_por_id(db, payload.id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")
        if producto.id_empresa != id_empresa:
            raise ValueError("El producto no pertenece a la empresa indicada.")

        tipo_movimiento = InventarioRepository.obtener_tipo_movimiento_por_id(
            db=db,
            id_tipo_movimiento=payload.id_tipo_movimiento,
        )
        if tipo_movimiento is None:
            raise LookupError("Tipo de movimiento no encontrado.")

        direccion = (tipo_movimiento.direccion or "").strip().lower()
        if direccion not in {"entrada", "salida"}:
            raise ValueError("La direccion del tipo de movimiento no es valida.")

        fecha_actual = datetime.now()
        stock = InventarioRepository.obtener_stock_por_producto_y_sucursal(
            db=db,
            id_producto=payload.id_producto,
            id_sucursal=id_sucursal,
        )
        if stock is None:
            stock = InventarioRepository.crear_stock(
                db=db,
                datos={
                    "id_producto": payload.id_producto,
                    "id_sucursal": id_sucursal,
                    "cantidad": 0,
                    "stock_minimo": 0,
                    "stock_maximo": 0,
                    "fecha_actualizacion": fecha_actual,
                },
            )

        nueva_cantidad = stock.cantidad + payload.cantidad if direccion == "entrada" else stock.cantidad - payload.cantidad
        if nueva_cantidad < 0:
            raise ValueError("Stock insuficiente para registrar la salida.")

        try:
            movimiento = InventarioRepository.crear_movimiento(
                db=db,
                datos={
                    "id_producto": payload.id_producto,
                    "id_tipo_movimiento": payload.id_tipo_movimiento,
                    "id_usuario": current_user.id_usuario,
                    "id_sucursal": id_sucursal,
                    "cantidad": payload.cantidad,
                    "observacion": payload.observacion,
                    "fecha_movimiento": fecha_actual,
                },
            )
            id_movimiento_creado = movimiento.id_movimiento_inventario
            stock = InventarioRepository.actualizar_stock(
                stock=stock,
                datos={
                    "cantidad": nueva_cantidad,
                    "fecha_actualizacion": fecha_actual,
                },
                db=db,
            )
            db.commit()

            if (
                stock.stock_minimo is not None
                and stock.cantidad <= stock.stock_minimo
                and stock.producto is not None
                and stock.sucursal is not None
            ):
                try:
                    NotificationService.enviar_alerta(
                        db=db,
                        id_empresa=id_empresa,
                        titulo=f'Stock bajo en "{stock.sucursal.nombre}"',
                        mensaje=(
                            f'El producto {stock.producto.nombre} tiene stock actual {stock.cantidad} '
                            f'y el stock minimo es {stock.stock_minimo} en {stock.sucursal.nombre}.'
                        ),
                        payload={
                            "id_producto": str(stock.id_producto),
                            "id_sucursal": str(stock.id_sucursal),
                            "nombre_sucursal": stock.sucursal.nombre,
                            "direccion_sucursal": stock.sucursal.direccion,
                            "nombre_producto": stock.producto.nombre,
                            "stock_actual": stock.cantidad,
                            "stock_minimo": stock.stock_minimo,
                            "unidad_medida": stock.producto.unidad_medida,
                        },
                    )
                except Exception:
                    # The stock movement must not fail if alert delivery has a problem.
                    pass
            # Use a fresh session to read the movimiento after commit to avoid
            # issues if the caller's session is in an aborted state.
            from app.core.database import SessionLocal

            read_session = SessionLocal()
            try:
                movimiento = InventarioRepository.obtener_movimiento_por_id(
                    db=read_session,
                    id_movimiento_inventario=id_movimiento_creado,
                )
            finally:
                read_session.close()
            return MovimientoInventarioResponse.model_validate(
                InventarioService._serializar_movimiento(
                    movimiento=movimiento,
                    stock_actual=stock.cantidad,
                )
            )
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def listar_movimientos_por_sucursal(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list[MovimientoInventarioResponse]:
        InventarioService._validar_empresa_y_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )

        movimientos = InventarioRepository.obtener_movimientos_por_sucursal(
            db=db,
            id_sucursal=id_sucursal,
            skip=skip,
            limit=limit,
        )

        # Construir el formato solicitado por el cliente
        from app.schemas.inventario_schema import (
            MovimientoListResponse,
            MovimientoProductoSimple,
            TipoMovimientoSimple,
        )

        resultados: list[MovimientoListResponse] = []
        for movimiento in movimientos:
            tipo_dir = (
                (movimiento.tipo_movimiento.direccion or "").strip().upper()
                if movimiento.tipo_movimiento is not None
                else ""
            )
            tipo_valor = "ENTRADA" if tipo_dir == "ENTRADA" else "SALIDA" if tipo_dir == "SALIDA" else tipo_dir

            producto_simple = MovimientoProductoSimple(
                id_producto=movimiento.id_producto,
                nombre=movimiento.producto.nombre if movimiento.producto is not None else "",
            )
            tipo_mov_simple = None
            if movimiento.tipo_movimiento is not None:
                tipo_mov_simple = TipoMovimientoSimple(
                    id_tipo_movimiento=movimiento.tipo_movimiento.id_tipo_movimiento,
                    nombre=movimiento.tipo_movimiento.nombre,
                )

            item = MovimientoListResponse(
                id_movimiento=movimiento.id_movimiento_inventario,
                id_producto=movimiento.id_producto,
                cantidad=movimiento.cantidad,
                observacion=movimiento.observacion,
                tipo=tipo_valor,
                producto=producto_simple,
                tipo_movimiento=tipo_mov_simple,
            )
            resultados.append(item)

        return resultados

    @staticmethod
    def sincronizar_stocks_iniciales(
        db: Session,
        fecha_actualizacion: datetime | None = None,
    ) -> None:
        InventarioRepository.sincronizar_stocks_iniciales(
            db=db,
            fecha_actualizacion=fecha_actualizacion,
        )

    @staticmethod
    def sincronizar_stocks_por_producto(
        db: Session,
        id_producto: int,
        id_empresa: int | None = None,
        fecha_actualizacion: datetime | None = None,
    ) -> None:
        InventarioRepository.sincronizar_stocks_por_producto(
            db=db,
            id_producto=id_producto,
            id_empresa=id_empresa,
            fecha_actualizacion=fecha_actualizacion,
        )

    @staticmethod
    def sincronizar_stocks_por_sucursal(
        db: Session,
        id_sucursal: int,
        fecha_actualizacion: datetime | None = None,
    ) -> None:
        InventarioRepository.sincronizar_stocks_por_sucursal(
            db=db,
            id_sucursal=id_sucursal,
            fecha_actualizacion=fecha_actualizacion,
        )

    @staticmethod
    def actualizar_stock_producto(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        id_producto: int,
        payload,
    ) -> StockProductoResponse:
        InventarioService._validar_empresa_y_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )

        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")
        if producto.id_empresa != id_empresa:
            raise ValueError("El producto no pertenece a la empresa indicada.")

        fecha_actual = datetime.now()
        stock = InventarioRepository.obtener_stock_por_producto_y_sucursal(
            db=db,
            id_producto=id_producto,
            id_sucursal=id_sucursal,
        )
        if stock is None:
            stock = InventarioRepository.crear_stock(
                db=db,
                datos={
                    "id_producto": id_producto,
                    "id_sucursal": id_sucursal,
                    "cantidad": 0,
                    "stock_minimo": payload.stock_minimo,
                    "stock_maximo": payload.stock_maximo,
                    "fecha_actualizacion": fecha_actual,
                },
            )
        else:
            stock = InventarioRepository.actualizar_stock(
                stock=stock,
                datos={
                    "stock_minimo": payload.stock_minimo,
                    "stock_maximo": payload.stock_maximo,
                    "fecha_actualizacion": fecha_actual,
                },
                db=db,
            )

        # Persistir cambios en la base y refrescar el objeto
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(stock)

        return StockProductoResponse.model_validate(InventarioService._serializar_stock(stock))
