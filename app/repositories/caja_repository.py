# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.empresas import Caja, CajaSesion, MovimientoCaja


class CajaRepository:
    @staticmethod
    def crear_caja(db: Session, datos: dict) -> Caja:
        caja = Caja(**datos)
        db.add(caja)
        db.flush()
        db.refresh(caja)
        return caja

    @staticmethod
    def obtener_cajas_por_sucursal(db: Session, id_sucursal: int) -> list[Caja]:
        return (
            db.query(Caja)
            .filter(Caja.id_sucursal == id_sucursal)
            .all()
        )

    @staticmethod
    def obtener_caja_por_sucursal(
        db: Session,
        id_sucursal: int,
        id_caja: int,
    ) -> Caja | None:
        return (
            db.query(Caja)
            .filter(
                Caja.id_sucursal == id_sucursal,
                Caja.id_caja == id_caja,
            )
            .first()
        )

    @staticmethod
    def obtener_caja_por_id(db: Session, id_caja: int) -> Caja | None:
        return db.query(Caja).filter(Caja.id_caja == id_caja).first()

    @staticmethod
    def obtener_sesion_abierta_por_usuario(
        db: Session,
        id_usuario: int,
    ) -> CajaSesion | None:
        return (
            db.query(CajaSesion)
            .filter(
                CajaSesion.id_usuario == id_usuario,
                CajaSesion.estado == "Abierto",
            )
            .first()
        )

    @staticmethod
    def obtener_caja_sesion_por_id(db: Session, id_caja_sesion: int) -> CajaSesion | None:
        return db.query(CajaSesion).filter(CajaSesion.id_caja_sesion == id_caja_sesion).first()

    @staticmethod
    def obtener_movimientos_por_caja_sesion(
        db: Session,
        id_caja_sesion: int,
    ) -> list[MovimientoCaja]:
        return (
            db.query(MovimientoCaja)
            .options(joinedload(MovimientoCaja.metodo_pago), joinedload(MovimientoCaja.tipo_movimiento_caja))
            .filter(MovimientoCaja.id_caja_sesion == id_caja_sesion)
            .order_by(MovimientoCaja.fecha.asc(), MovimientoCaja.id_movimiento_caja.asc())
            .all()
        )

    @staticmethod
    def obtener_sesion_abierta_por_caja(
        db: Session,
        id_caja: int,
    ) -> CajaSesion | None:
        return (
            db.query(CajaSesion)
            .filter(
                CajaSesion.id_caja == id_caja,
                CajaSesion.estado == "Abierto",
            )
            .first()
        )

    @staticmethod
    def crear_caja_sesion(db: Session, datos: dict) -> CajaSesion:
        caja_sesion = CajaSesion(**datos)
        db.add(caja_sesion)
        db.flush()
        db.refresh(caja_sesion)
        return caja_sesion

    @staticmethod
    def actualizar_caja(caja: Caja, datos: dict, db: Session) -> Caja:
        for campo, valor in datos.items():
            setattr(caja, campo, valor)

        db.commit()
        db.refresh(caja)
        return caja
