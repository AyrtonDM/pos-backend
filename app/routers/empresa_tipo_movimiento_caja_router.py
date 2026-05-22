from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.empresas import TipoMovimientoCaja
from app.schemas.tipo_movimiento_caja_schema import TipoMovimientoCajaResponse

tipo_movimiento_caja_router = APIRouter(prefix="/api/empresas", tags=["empresas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@tipo_movimiento_caja_router.get(
    "/tipos-movimiento-caja",
    response_model=list[TipoMovimientoCajaResponse],
)
def listar_tipos_movimiento_caja(db: Session = Depends(get_db)):
    try:
        tipos = (
            db.query(TipoMovimientoCaja)
            .order_by(TipoMovimientoCaja.id_tipo_movimiento_caja.asc())
            .all()
        )
        return tipos
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar tipos de movimiento de caja.")