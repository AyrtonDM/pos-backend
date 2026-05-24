# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.empresas import MovimientoCaja


class MovimientoCajaRepository:
    @staticmethod
    def crear_movimiento(db: Session, datos: dict) -> MovimientoCaja:
        movimiento = MovimientoCaja(**datos)
        db.add(movimiento)
        db.flush()
        db.refresh(movimiento)
        return movimiento
