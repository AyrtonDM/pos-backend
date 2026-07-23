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
    try:
        planes = PlanService.listar_planes(db=db)
        print(f"[PLANES] encontrados={len(planes)}", flush=True)
        return planes
    except Exception as e:
        import traceback
        print(f"[PLANES ERROR] {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar los planes: {str(e)}"
        )