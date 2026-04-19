# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.empresa_schema import EmpresaCreate, EmpresaResponse, EmpresaUpdate
from app.services.empresa_service import EmpresaService

router = APIRouter(prefix="/api/empresas", tags=["empresas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/mis-empresas", response_model=list[EmpresaResponse])
def obtener_empresas_del_usuario(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.obtener_empresas_del_usuario(
            db=db,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las empresas.")


@router.get("/{id_empresa}", response_model=EmpresaResponse)
def obtener_empresa_del_usuario(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.obtener_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la empresa.")


@router.put("/{id_empresa}", response_model=EmpresaResponse)
def actualizar_empresa(
    id_empresa: int,
    datos: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.actualizar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            razon_social=datos.razon_social,
            nit=datos.nit,
            correo=datos.correo,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la empresa.")


@router.post("/crear", response_model=dict)
def crear_empresa(
    datos: EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.crear_empresa_para_usuario(
            db=db,
            current_user=current_user,
            nombre=datos.nombre,
            razon_social=datos.razon_social,
            nit=datos.nit,
            correo=datos.correo,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la empresa.")
