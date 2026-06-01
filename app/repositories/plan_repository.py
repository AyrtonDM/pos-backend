# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.empresas.plan import Plan


class PlanRepository:
    @staticmethod
    def listar_planes(db: Session) -> list[Plan]:
        return db.query(Plan).all()
