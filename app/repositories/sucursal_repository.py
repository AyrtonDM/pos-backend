# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.empresas import Sucursal


class SucursalRepository:
    @staticmethod
    def crear_sucursal(db: Session, datos: dict) -> Sucursal:
        sucursal = Sucursal(**datos)
        db.add(sucursal)
        db.flush()
        db.refresh(sucursal)
        return sucursal

    @staticmethod
    def obtener_sucursales_por_empresa(db: Session, id_empresa: int) -> list[Sucursal]:
        return db.query(Sucursal).filter(Sucursal.id_empresa == id_empresa).all()

    @staticmethod
    def obtener_sucursal_por_empresa(
        db: Session,
        id_empresa: int,
        id_sucursal: int,
    ) -> Sucursal | None:
        return (
            db.query(Sucursal)
            .filter(
                Sucursal.id_empresa == id_empresa,
                Sucursal.id_sucursal == id_sucursal,
            )
            .first()
        )

    @staticmethod
    def obtener_sucursal_por_id(db: Session, id_sucursal: int) -> Sucursal | None:
        return (
            db.query(Sucursal)
            .filter(Sucursal.id_sucursal == id_sucursal)
            .first()
        )

    @staticmethod
    def actualizar_sucursal(sucursal: Sucursal, datos: dict, db: Session) -> Sucursal:
        for campo, valor in datos.items():
            setattr(sucursal, campo, valor)

        db.commit()
        db.refresh(sucursal)
        return sucursal
