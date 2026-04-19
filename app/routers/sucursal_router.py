# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.sucursal_schema import (
    EmpleadoSucursalResponse,
    InvitacionEmpleadoCreate,
    SucursalEmpleadoAsignadaResponse,
    SucursalCreate,
    SucursalResponse,
    SucursalUpdate,
)
from app.services.sucursal_service import SucursalService

empresa_router = APIRouter(prefix="/api/empresas", tags=["sucursales"])
sucursal_router = APIRouter(prefix="/api/sucursales", tags=["sucursales"])
invitacion_router = APIRouter(prefix="/api/invitaciones", tags=["invitaciones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@empresa_router.post("/{id_empresa}/sucursales", response_model=SucursalResponse)
def crear_sucursal(
    id_empresa: int,
    datos: SucursalCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.crear_sucursal_para_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la sucursal.")


@empresa_router.get("/{id_empresa}/sucursales", response_model=list[SucursalResponse])
def obtener_sucursales(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursales_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las sucursales.")


@empresa_router.get(
    "/{id_empresa}/sucursales/{id_sucursal}",
    response_model=SucursalResponse,
)
def obtener_sucursal(
    id_empresa: int,
    id_sucursal: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursal_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la sucursal.")


@empresa_router.post("/{id_empresa}/sucursales/{id_sucursal}/invitar-empleado")
def invitar_empleado(
    id_empresa: int,
    id_sucursal: int,
    datos: InvitacionEmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.enviar_invitacion_empleado(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            email=datos.email,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al enviar la invitacion.")


@empresa_router.get(
    "/{id_empresa}/sucursales/{id_sucursal}/empleados",
    response_model=list[EmpleadoSucursalResponse],
)
def obtener_empleados_sucursal(
    id_empresa: int,
    id_sucursal: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_empleados_de_sucursal(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los empleados.")


@sucursal_router.put("/{id_sucursal}", response_model=SucursalResponse)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.actualizar_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_sucursal=id_sucursal,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la sucursal.")


@sucursal_router.get(
    "/mis-sucursales-empleado",
    response_model=list[SucursalEmpleadoAsignadaResponse],
)
def obtener_mis_sucursales_empleado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursales_asignadas_como_empleado(
            db=db,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las sucursales.")


@invitacion_router.get("/empleado/aceptar/{id_empresa}/{id_sucursal}/{id_usuario}")
def aceptar_invitacion_empleado(
    id_empresa: int,
    id_sucursal: int,
    id_usuario: int,
    db: Session = Depends(get_db),
):
    try:
        return SucursalService.aceptar_invitacion_empleado(
            db=db,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_usuario=id_usuario,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al aceptar la invitacion.")
