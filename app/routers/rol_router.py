from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.rol_schema import RolCreateRequest, RolCreateResponse, RolDetalleResponse, RolResponse, RolUpdateRequest
from app.services.rol_service import RolService
from app.services.bitacora_service import registrar_accion

router = APIRouter(prefix="/api/roles", tags=["roles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/empresa/{id_empresa}", response_model=list[RolResponse])
def listar_roles(
    id_empresa: int,
    db: Session = Depends(get_db),
):
    try:
        return RolService.listar_roles(db=db, id_empresa=id_empresa)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar los roles.")


@router.get("/{id_rol}", response_model=RolDetalleResponse)
def obtener_rol_por_id(
    id_rol: int,
    db: Session = Depends(get_db),
):
    try:
        return RolService.obtener_rol_por_id(db=db, id_rol=id_rol)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el rol.")


@router.put("/{id_rol}", response_model=RolDetalleResponse)
def editar_rol(
    id_rol: int,
    payload: RolUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        resultado = RolService.editar_rol(
            db=db,
            id_rol=id_rol,
            activo=payload.activo,
            permiso_ids=payload.permiso_ids,
        )
        try:
            registrar_accion(
                usuario_nombre="UsuarioDesconocido",
                accion=f"Editó rol ID: {id_rol}",
                empresa_nombre=str(resultado.id_empresa) if resultado and hasattr(resultado, 'id_empresa') else None
            )
        except Exception:
            pass
        return resultado
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al editar el rol.")


@router.post("/empresa/{id_empresa}", response_model=RolCreateResponse, status_code=201)
def crear_rol(
    id_empresa: int,
    payload: RolCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        resultado = RolService.crear_rol_con_permisos(
            db=db,
            id_empresa=id_empresa,
            nombre=payload.nombre,
            permiso_ids=payload.permiso_ids,
        )
        try:
            registrar_accion(
                usuario_nombre="UsuarioDesconocido",
                accion=f"Registró rol: {payload.nombre}",
                empresa_nombre=str(id_empresa)
            )
        except Exception:
            pass
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el rol.")