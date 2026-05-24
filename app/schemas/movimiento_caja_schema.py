from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MovimientoCajaCreate(BaseModel):
    concepto: str | None = None
    monto: Decimal
    id_tipo_movimiento_caja: int
    id_metodo_pago: int | None = None


class MovimientoCajaResponse(BaseModel):
    id_movimiento_caja: int
    id_metodo_pago: int | None
    id_tipo_movimiento_caja: int
    id_caja_sesion: int
    id_usuario: int
    fecha: datetime
    monto: Decimal
    concepto: str | None

    class Config:
        from_attributes = True
