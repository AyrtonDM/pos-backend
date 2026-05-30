from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.bitacora_schema import BitacoraResponse
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/api/bitacora", tags=["bitacora"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=dict)
def obtener_bitacora(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Registros a retornar"),
    id_usuario: int | None = Query(None, description="Filtrar por usuario"),
    modulo: str | None = Query(None, description="Filtrar por módulo"),
    accion: str | None = Query(None, description="Filtrar por acción"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtiene el historial de la bitácora.

    Parámetros:
    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Número de registros a retornar (máx 100)
    - **id_usuario**: Filtrar por ID de usuario
    - **modulo**: Filtrar por módulo (usuarios, productos, ventas, etc)
    - **accion**: Filtrar por acción (CREATE, UPDATE, DELETE, LOGIN, etc)

    Requiere autenticación.
    """
    try:
        resultado = AuditoriaService.obtener_bitacora(
            db=db,
            skip=skip,
            limit=limit,
            id_usuario=id_usuario,
            modulo=modulo,
            accion=accion,
        )

        # Convertir registros a schema
        registros_response = [
            BitacoraResponse.model_validate(registro) for registro in resultado["registros"]
        ]

        return {
            "registros": registros_response,
            "total": resultado["total"],
            "skip": resultado["skip"],
            "limit": resultado["limit"],
            "paginas": resultado["paginas"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener bitácora")


@router.get("/usuario/{id_usuario}", response_model=dict)
def obtener_bitacora_usuario(
    id_usuario: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtiene el historial de bitácora de un usuario específico.

    Requiere autenticación.
    """
    try:
        resultado = AuditoriaService.obtener_bitacora(
            db=db, skip=skip, limit=limit, id_usuario=id_usuario
        )

        registros_response = [
            BitacoraResponse.model_validate(registro) for registro in resultado["registros"]
        ]

        return {
            "usuario_id": id_usuario,
            "registros": registros_response,
            "total": resultado["total"],
            "skip": resultado["skip"],
            "limit": resultado["limit"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener bitácora del usuario")
