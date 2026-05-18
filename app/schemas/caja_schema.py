from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CajaCreate(BaseModel):
    nombre: str
    codigo: str


class CajaUpdate(BaseModel):
    nombre: str
    codigo: str
    activo: bool


class CajaResponse(BaseModel):
    id_caja: int
    id_sucursal: int
    nombre: str
    codigo: str
    fecha_creacion: date
    activo: bool

    class Config:
        from_attributes = True


class CajaSesionCreate(BaseModel):
    monto_inicial: Decimal
    nota: str | None = None


class CajaSesionResponse(BaseModel):
    id_caja_sesion: int
    id_caja: int
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    monto_inicial: Decimal
    monto_final: Decimal | None
    estado: str
    nota: str | None

    class Config:
        from_attributes = True
