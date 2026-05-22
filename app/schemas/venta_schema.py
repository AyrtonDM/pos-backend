from pydantic import BaseModel


class TipoVentaResponse(BaseModel):
    id_tipo_venta: int
    nombre: str
    descripcion: str | None

    class Config:
        from_attributes = True


class MetodoPagoResponse(BaseModel):
    id_metodo_pago: int
    nombre: str
    descripcion: str | None

    class Config:
        from_attributes = True