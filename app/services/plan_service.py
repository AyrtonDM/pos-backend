# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.repositories.plan_repository import PlanRepository


class PlanService:
    @staticmethod
    def listar_planes(db: Session):
        return PlanRepository.listar_planes(db=db)
