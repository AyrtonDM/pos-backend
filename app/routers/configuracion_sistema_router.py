# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios.usuario import Usuario
from app.schemas.configuracion_sistema_schema import (
    ConfiguracionSistemaResponse,
    ConfiguracionSistemaUpdate,
)
from app.services.configuracion_sistema_service import ConfiguracionSistemaService

router = APIRouter(prefix="/api/configuracion-sistema", tags=["configuracion-sistema"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/empresas/{id_empresa}", response_model=ConfiguracionSistemaResponse)
def obtener_configuracion(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ConfiguracionSistemaService.obtener_configuracion(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la configuración: {str(e)}")

@router.put("/empresas/{id_empresa}", response_model=ConfiguracionSistemaResponse)
def actualizar_configuracion(
    id_empresa: int,
    datos: ConfiguracionSistemaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ConfiguracionSistemaService.actualizar_configuracion(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            datos=datos.dict(),
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la configuración: {str(e)}")
