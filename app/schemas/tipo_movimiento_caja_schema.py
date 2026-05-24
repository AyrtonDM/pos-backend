from pydantic import BaseModel


class TipoMovimientoCajaResponse(BaseModel):
    id_tipo_movimiento_caja: int
    nombre: str
    descripcion: str | None

    class Config:
        from_attributes = True