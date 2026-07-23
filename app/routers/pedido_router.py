from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user, get_db
from app.models.usuarios import Usuario
from app.schemas.pedido_schema import (
    PedidoClienteCreate,
    PedidoClienteEstadoUpdate,
    PedidoClienteResponse,
)
from app.services.pedido_service import PedidoService

pedido_router = APIRouter(prefix="/api/pedidos", tags=["pedidos"])


# ─── ENDPOINTS CLIENTE (Flutter) ─────────────────────────────────────────────

@pedido_router.get(
    "/me",
    response_model=List[PedidoClienteResponse],
    summary="Lista los pedidos del cliente autenticado",
)
def obtener_mis_pedidos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.obtener_pedidos_cliente(db=db, current_user=current_user)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los pedidos.")


@pedido_router.get(
    "/me/{id_pedido}",
    response_model=PedidoClienteResponse,
    summary="Detalle de un pedido propio",
)
def obtener_mi_pedido(
    id_pedido: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.obtener_pedido_propio(
            db=db, current_user=current_user, id_pedido=id_pedido
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el pedido.")

@pedido_router.patch(
    "/me/{id_pedido}/cancelar",
    response_model=PedidoClienteResponse,
    summary="Cancela un pedido (solo si está enviado o en revisión)",
)
def cancelar_mi_pedido(
    id_pedido: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.cancelar_pedido_cliente(
            db=db, current_user=current_user, id_pedido=id_pedido
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al cancelar el pedido.")


@pedido_router.post(
    "/empresas/{id_empresa}",
    response_model=PedidoClienteResponse,
    summary="Crea un pedido hacia una empresa (como cliente)",
)
def crear_pedido_empresa(
    id_empresa: int,
    payload: PedidoClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.crear_pedido(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            payload=payload,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        detail = e.args[0] if e.args else str(e)
        raise HTTPException(status_code=400, detail=detail)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el pedido.")


# ─── ENDPOINTS CAJERO / ADMINISTRADOR (Angular) ──────────────────────────────

@pedido_router.get(
    "/empresas/{id_empresa}",
    response_model=List[PedidoClienteResponse],
    summary="Lista pedidos de la empresa. Filtrable por sucursal_id y estado.",
)
def obtener_pedidos_de_empresa(
    id_empresa: int,
    sucursal_id: Optional[int] = Query(None, description="Filtrar por sucursal"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.obtener_pedidos_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=sucursal_id,
            estado=estado,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los pedidos.")


@pedido_router.get(
    "/empresas/{id_empresa}/{id_pedido}",
    response_model=PedidoClienteResponse,
    summary="Detalle operativo de un pedido (Cajero/Admin)",
)
def obtener_detalle_pedido_empresa(
    id_empresa: int,
    id_pedido: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.obtener_pedido_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_pedido=id_pedido,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el pedido.")


@pedido_router.patch(
    "/empresas/{id_empresa}/{id_pedido}/estado",
    response_model=PedidoClienteResponse,
    summary="Cambia el estado del pedido, validando la maquina de estados",
)
def actualizar_estado_pedido(
    id_empresa: int,
    id_pedido: int,
    payload: PedidoClienteEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return PedidoService.actualizar_estado_pedido(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_pedido=id_pedido,
            payload=payload,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar estado del pedido.")
