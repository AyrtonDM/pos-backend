# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.plan_schema import PlanResponse
from app.services.plan_service import PlanService

router = APIRouter(prefix="/api/planes", tags=["planes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[PlanResponse])
def listar_planes(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los planes de suscripción disponibles.
    """
    try:
        return PlanService.listar_planes(db=db)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar los planes.")
