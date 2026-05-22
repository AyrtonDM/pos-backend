from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ventas import MetodoPago, TipoVenta
from app.schemas.venta_schema import MetodoPagoResponse, TipoVentaResponse

venta_router = APIRouter(prefix="/api/ventas", tags=["ventas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@venta_router.get("/tipos-venta", response_model=list[TipoVentaResponse])
def listar_tipos_venta(db: Session = Depends(get_db)):
    try:
        tipos = (
            db.query(TipoVenta)
            .order_by(TipoVenta.id_tipo_venta.asc())
            .all()
        )
        return tipos
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar tipos de venta.")


@venta_router.get("/metodos-pago", response_model=list[MetodoPagoResponse])
def listar_metodos_pago(db: Session = Depends(get_db)):
    try:
        metodos = (
            db.query(MetodoPago)
            .order_by(MetodoPago.id_metodo_pago.asc())
            .all()
        )
        return metodos
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar metodos de pago.")