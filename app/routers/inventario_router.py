from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.inventario_schema import (
    MovimientoInventarioCreate,
    MovimientoInventarioResponse,
    StockProductoResponse,
    StockUpdateRequest,
    TipoMovimientoResponse,
)
from app.schemas.inventario_schema import MovimientoListResponse
from app.services.inventario_service import InventarioService

router = APIRouter(prefix="/api/inventario", tags=["inventario"])

logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/tipos-movimiento", response_model=list[TipoMovimientoResponse])
def listar_tipos_movimiento(db: Session = Depends(get_db)):
    try:
        return InventarioService.listar_tipos_movimiento(db=db)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar tipos de movimiento.")


@router.post(
    "/empresas/{id_empresa}/sucursales/{id_sucursal}/movimientos",
    response_model=MovimientoInventarioResponse,
)
def crear_movimiento(
    id_empresa: int,
    id_sucursal: int,
    datos: MovimientoInventarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Log incoming request for debugging (temporary)
    try:
        user_id = getattr(current_user, 'id_usuario', None)
    except Exception:
        user_id = None
    logger.debug(
        "crear_movimiento called: empresa=%s sucursal=%s user=%s datos=%s",
        id_empresa,
        id_sucursal,
        user_id,
        str(datos),
    )
    try:
        return InventarioService.crear_movimiento(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            payload=datos,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Error al crear movimiento para empresa=%s sucursal=%s", id_empresa, id_sucursal)
        raise HTTPException(status_code=500, detail="Error al registrar el movimiento.")


@router.get(
    "/empresas/{id_empresa}/sucursales/{id_sucursal}/stock",
    response_model=list[StockProductoResponse],
)
def listar_stock_sucursal(
    id_empresa: int,
    id_sucursal: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return InventarioService.listar_stock_por_sucursal(
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
        raise HTTPException(status_code=500, detail="Error al listar el stock.")


@router.get(
    "/empresas/{id_empresa}/sucursales/{id_sucursal}/movimientos",
    response_model=list[MovimientoListResponse],
)
def listar_movimientos_sucursal(
    id_empresa: int,
    id_sucursal: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return InventarioService.listar_movimientos_por_sucursal(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            skip=skip,
            limit=limit,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar movimientos de inventario.")


@router.put(
    "/empresas/{id_empresa}/sucursales/{id_sucursal}/stock/{id_producto}",
    response_model=StockProductoResponse,
)
def actualizar_stock_producto(
    id_empresa: int,
    id_sucursal: int,
    id_producto: int,
    datos: StockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return InventarioService.actualizar_stock_producto(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_producto=id_producto,
            payload=datos,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar el stock.")
