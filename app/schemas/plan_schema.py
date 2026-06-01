# -*- coding: utf-8 -*-
from decimal import Decimal

from pydantic import BaseModel


class PlanResponse(BaseModel):
    id_plan: int
    nombre: str
    descripcion: str
    precio: Decimal

    class Config:
        from_attributes = True
