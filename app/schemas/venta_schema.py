from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List



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


class DetalleVentaCreate(BaseModel):
    id_producto: int
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal | None = Decimal("0.00")
    subtotal: Decimal
    descripcion: str | None = None


class VentaPagoCreate(BaseModel):
    id_metodo_pago: int
    monto: Decimal


class VentaCreate(BaseModel):
    id_tipo_venta: int
    id_cliente: int | None = None
    id_metodo_pago: int | None = None
    pagos: List[VentaPagoCreate] | None = None
    subtotal: Decimal
    descuento_total: Decimal | None = Decimal("0.00")
    total: Decimal
    estado: str | None = "Pendiente"
    detalles: List[DetalleVentaCreate]


class DetalleVentaResponse(DetalleVentaCreate):
    id_detalle_venta: int

    class Config:
        from_attributes = True


class VentaPagoResponse(BaseModel):
    id_metodo_pago: int
    monto: Decimal
    fecha: datetime
    metodo_pago: MetodoPagoResponse | None = None

    class Config:
        from_attributes = True


class VentaResponse(BaseModel):
    id_venta: int
    id_usuario: int
    id_caja_sesion: int
    subtotal: Decimal
    descuento_total: Decimal | None
    total: Decimal
    fecha: datetime
    estado: str
    id_metodo_pago: int | None = None
    metodo_pago: MetodoPagoResponse | None = None
    detalles: List[DetalleVentaResponse]
    pagos: List[VentaPagoResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
