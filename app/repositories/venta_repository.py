from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.empresas import Caja, CajaSesion, Sucursal
from app.models.ventas import CuentaPorCobrar, DetalleVenta, PagoCredito, Venta, VentaPago


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
    def crear_cuenta_por_cobrar(db: Session, datos: dict) -> CuentaPorCobrar:
        cuenta_por_cobrar = CuentaPorCobrar(**datos)
        db.add(cuenta_por_cobrar)
        db.flush()
        db.refresh(cuenta_por_cobrar)
        return cuenta_por_cobrar

    @staticmethod
    def crear_pago_credito(db: Session, datos: dict) -> PagoCredito:
        pago_credito = PagoCredito(**datos)
        db.add(pago_credito)
        db.flush()
        db.refresh(pago_credito)
        return pago_credito

    @staticmethod
    def obtener_cuenta_por_cobrar_para_actualizar(
        db: Session,
        id_cxc: int,
    ) -> CuentaPorCobrar | None:
        return (
            db.query(CuentaPorCobrar)
            .filter(CuentaPorCobrar.id_cxc == id_cxc)
            .with_for_update()
            .first()
        )

    @staticmethod
    def obtener_venta_por_id(db: Session, id_venta: int) -> Venta | None:
        return (
            db.query(Venta)
            .options(
                joinedload(Venta.tipo_venta),
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
                joinedload(Venta.tipo_venta),
                joinedload(Venta.detalles),
                joinedload(Venta.pagos).joinedload(VentaPago.metodo_pago),
            )
            .filter(Venta.id_caja_sesion == id_caja_sesion)
            .order_by(Venta.fecha.desc())
            .all()
        )

    @staticmethod
    def obtener_cuentas_por_cobrar_por_empresa_y_cliente(
        db: Session,
        id_empresa: int,
        id_cliente: int,
    ) -> list[CuentaPorCobrar]:
        return (
            db.query(CuentaPorCobrar)
            .join(CuentaPorCobrar.venta)
            .join(Venta.caja_sesion)
            .join(CajaSesion.caja)
            .join(Caja.sucursal)
            .options(
                joinedload(CuentaPorCobrar.venta).joinedload(Venta.tipo_venta),
                joinedload(CuentaPorCobrar.venta)
                .selectinload(Venta.detalles)
                .joinedload(DetalleVenta.producto),
                selectinload(CuentaPorCobrar.pagos_credito).joinedload(
                    PagoCredito.metodo_pago
                ),
            )
            .filter(
                Sucursal.id_empresa == id_empresa,
                Venta.id_cliente == id_cliente,
            )
            .order_by(CuentaPorCobrar.fecha_inicio.desc(), CuentaPorCobrar.id_cxc.desc())
            .all()
        )
