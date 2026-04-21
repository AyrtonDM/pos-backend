from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.models.inventario.movimiento_inventario import MovimientoInventario
from app.models.inventario.stock import Stock
from app.models.inventario.tipo_movimiento import TipoMovimiento


class InventarioRepository:
    @staticmethod
    def obtener_tipos_movimiento(db: Session) -> list[TipoMovimiento]:
        return (
            db.query(TipoMovimiento)
            .order_by(TipoMovimiento.id_tipo_movimiento.asc())
            .all()
        )

    @staticmethod
    def obtener_tipo_movimiento_por_id(
        db: Session,
        id_tipo_movimiento: int,
    ) -> TipoMovimiento | None:
        return (
            db.query(TipoMovimiento)
            .filter(TipoMovimiento.id_tipo_movimiento == id_tipo_movimiento)
            .first()
        )

    @staticmethod
    def obtener_stock_por_producto_y_sucursal(
        db: Session,
        id_producto: int,
        id_sucursal: int,
    ) -> Stock | None:
        return (
            db.query(Stock)
            .filter(
                Stock.id_producto == id_producto,
                Stock.id_sucursal == id_sucursal,
            )
            .first()
        )

    @staticmethod
    def obtener_stocks_por_sucursal(
        db: Session,
        id_sucursal: int,
    ) -> list[Stock]:
        return (
            db.query(Stock)
            .options(joinedload(Stock.producto))
            .filter(Stock.id_sucursal == id_sucursal)
            .order_by(Stock.id_stock.asc())
            .all()
        )

    @staticmethod
    def crear_stock(db: Session, datos: dict) -> Stock:
        stock = Stock(**datos)
        db.add(stock)
        db.flush()
        db.refresh(stock)
        return stock

    @staticmethod
    def actualizar_stock(stock: Stock, datos: dict, db: Session) -> Stock:
        for campo, valor in datos.items():
            setattr(stock, campo, valor)
        db.flush()
        db.refresh(stock)
        return stock

    @staticmethod
    def crear_movimiento(db: Session, datos: dict) -> MovimientoInventario:
        movimiento = MovimientoInventario(**datos)
        db.add(movimiento)
        db.flush()
        db.refresh(movimiento)
        return movimiento

    @staticmethod
    def obtener_movimiento_por_id(
        db: Session,
        id_movimiento_inventario: int,
    ) -> MovimientoInventario | None:
        return (
            db.query(MovimientoInventario)
            .options(joinedload(MovimientoInventario.tipo_movimiento))
            .filter(MovimientoInventario.id_movimiento_inventario == id_movimiento_inventario)
            .first()
        )

    @staticmethod
    def sincronizar_stocks_por_producto(
        db: Session,
        id_producto: int,
        id_empresa: int | None = None,
        fecha_actualizacion: datetime | None = None,
    ) -> None:
        fecha_actualizacion = fecha_actualizacion or datetime.now()
        db.execute(
            text(
                """
                INSERT INTO stock (
                    id_producto,
                    id_sucursal,
                    cantidad,
                    stock_minimo,
                    stock_maximo,
                    fecha_actualizacion
                )
                SELECT
                    :id_producto,
                    s.id_sucursal,
                    0,
                    0,
                    0,
                    :fecha_actualizacion
                FROM sucursal s
                WHERE (:id_empresa IS NULL OR s.id_empresa = :id_empresa)
                AND NOT EXISTS (
                    SELECT 1
                    FROM stock st
                    WHERE st.id_producto = :id_producto
                      AND st.id_sucursal = s.id_sucursal
                )
                """
            ),
            {
                "id_producto": id_producto,
                "id_empresa": id_empresa,
                "fecha_actualizacion": fecha_actualizacion,
            },
        )

    @staticmethod
    def sincronizar_stocks_por_sucursal(
        db: Session,
        id_sucursal: int,
        fecha_actualizacion: datetime | None = None,
    ) -> None:
        fecha_actualizacion = fecha_actualizacion or datetime.now()
        db.execute(
            text(
                """
                INSERT INTO stock (
                    id_producto,
                    id_sucursal,
                    cantidad,
                    stock_minimo,
                    stock_maximo,
                    fecha_actualizacion
                )
                SELECT
                    p.id_producto,
                    :id_sucursal,
                    0,
                    0,
                    0,
                    :fecha_actualizacion
                FROM producto p
                JOIN sucursal s
                  ON s.id_sucursal = :id_sucursal
                 AND s.id_empresa = p.id_empresa
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM stock st
                    WHERE st.id_producto = p.id_producto
                      AND st.id_sucursal = :id_sucursal
                )
                """
            ),
            {
                "id_sucursal": id_sucursal,
                "fecha_actualizacion": fecha_actualizacion,
            },
        )

    @staticmethod
    def sincronizar_stocks_iniciales(
        db: Session,
        fecha_actualizacion: datetime | None = None,
    ) -> None:
        fecha_actualizacion = fecha_actualizacion or datetime.now()
        db.execute(
            text(
                """
                INSERT INTO stock (
                    id_producto,
                    id_sucursal,
                    cantidad,
                    stock_minimo,
                    stock_maximo,
                    fecha_actualizacion
                )
                SELECT
                    p.id_producto,
                    s.id_sucursal,
                    0,
                    0,
                    0,
                    :fecha_actualizacion
                FROM producto p
                JOIN sucursal s
                  ON s.id_empresa = p.id_empresa
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM stock st
                    WHERE st.id_producto = p.id_producto
                      AND st.id_sucursal = s.id_sucursal
                )
                """
            ),
            {
                "fecha_actualizacion": fecha_actualizacion,
            },
        )
