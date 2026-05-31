from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.empresas import Empresa
from app.models.usuarios import Usuario
from app.schemas.reporte_schema import (
    PlantillaReporte,
    RespuestaInterpretacion,
    RespuestaReporte,
    SolicitudReporte,
)
from app.services.reportes_service import ReportesService

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/plantillas", response_model=list[PlantillaReporte])
@router.get("/templates", response_model=list[PlantillaReporte])
def listar_plantillas(_: Usuario = Depends(get_current_user)):
    return ReportesService.obtener_catalogo()


@router.post("/{empresa_id}/interpretar", response_model=RespuestaInterpretacion)
@router.post("/{empresa_id}/interpret", response_model=RespuestaInterpretacion)
def interpretar_reporte(
    empresa_id: int,
    solicitud: SolicitudReporte,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id_empresa == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="La empresa no existe.")

    especificacion, advertencias = ReportesService.interpretar_solicitud(solicitud)
    plantilla = next(
        (item for item in ReportesService.obtener_catalogo() if item.identificador == especificacion.identificador_plantilla),
        None,
    )
    return RespuestaInterpretacion(
        especificacion=especificacion,
        plantilla=plantilla,
        advertencias=advertencias,
    )


@router.post("/{empresa_id}/ejecutar", response_model=RespuestaReporte)
@router.post("/{empresa_id}/run", response_model=RespuestaReporte)
def ejecutar_reporte(
    empresa_id: int,
    solicitud: SolicitudReporte,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id_empresa == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="La empresa no existe.")

    try:
        return ReportesService.ejecutar_reporte(db=db, solicitud=solicitud, empresa_id=empresa_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el reporte: {exc}") from exc