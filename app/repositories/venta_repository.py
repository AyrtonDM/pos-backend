from sqlalchemy.orm import Session, joinedload

from app.models.ventas import Venta, DetalleVenta, VentaPago


class VentaRepository:
    @staticmethod
    def crear_venta(db: Session, datos: dict) -> Venta:
        venta = Venta(**datos)
        db.add(venta)
        db.flush()
        db.refresh(venta)
        return venta

    @staticmethod
    def crear_detalle(db: Session, datos: dict) -> DetalleVenta:
        detalle = DetalleVenta(**datos)
        db.add(detalle)
        db.flush()
        db.refresh(detalle)
        return detalle

    @staticmethod
    def crear_venta_pago(db: Session, datos: dict) -> VentaPago:
        venta_pago = VentaPago(**datos)
        db.add(venta_pago)
        db.flush()
        db.refresh(venta_pago)
        return venta_pago

    @staticmethod
    def obtener_venta_por_id(db: Session, id_venta: int) -> Venta | None:
        return (
            db.query(Venta)
            .options(
                joinedload(Venta.detalles),
                joinedload(Venta.pagos).joinedload(VentaPago.metodo_pago),
            )
            .filter(Venta.id_venta == id_venta)
            .first()
        )

    @staticmethod
    def obtener_ventas_por_caja_sesion(db: Session, id_caja_sesion: int) -> list[Venta]:
        return (
            db.query(Venta)
            .options(
                joinedload(Venta.detalles),
                joinedload(Venta.pagos).joinedload(VentaPago.metodo_pago),
            )
            .filter(Venta.id_caja_sesion == id_caja_sesion)
            .order_by(Venta.fecha.desc())
            .all()
        )
