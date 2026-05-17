# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.empresas import Caja


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
    def actualizar_caja(caja: Caja, datos: dict, db: Session) -> Caja:
        for campo, valor in datos.items():
            setattr(caja, campo, valor)

        db.commit()
        db.refresh(caja)
        return caja
