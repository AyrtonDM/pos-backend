from datetime import datetime

from pydantic import BaseModel


class BitacoraResponse(BaseModel):
    id_bitacora: int
    id_usuario: int | None
    accion: str
    modulo: str
    descripcion: str | None
    ip: str | None
    fecha_hora: datetime

    class Config:
        from_attributes = True


class BitacoraCreate(BaseModel):
    id_usuario: int | None
    accion: str
    modulo: str
    descripcion: str | None = None
    ip: str | None = None
