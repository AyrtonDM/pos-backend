from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.inventario_schema import (
    MovimientoInventarioCreate,
    MovimientoInventarioResponse,
    StockProductoResponse,
    TipoMovimientoResponse,
)
from app.services.inventario_service import InventarioService

router = APIRouter(prefix="/api/inventario", tags=["inventario"])


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
