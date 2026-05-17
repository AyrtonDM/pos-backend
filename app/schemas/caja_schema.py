from datetime import date

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
