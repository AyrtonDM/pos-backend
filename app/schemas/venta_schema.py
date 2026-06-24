from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List

from app.schemas.movimiento_caja_schema import MovimientoCajaResponse



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


class PagoCreditoCreate(BaseModel):
    id_metodo_pago: int = Field(gt=0)
    monto_pagado: Decimal = Field(gt=Decimal("0.00"))


class CobroCuentaPorCobrarCreate(BaseModel):
    id_cxc: int = Field(gt=0)
    pagos_credito: list[PagoCreditoCreate] = Field(min_length=1)


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


class VentaCreateResponse(BaseModel):
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


class VentaResponse(VentaCreateResponse):
    tipo_venta_nombre: str | None = None


class ProductoDetalleCreditoResponse(BaseModel):
    id_producto: int
    nombre: str
    codigo_barra: str | None
    unidad_medida: str

    class Config:
        from_attributes = True


class DetalleVentaCreditoResponse(BaseModel):
    id_detalle_venta: int
    id_producto: int
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    subtotal: Decimal
    total: Decimal
    descripcion: str | None
    producto: ProductoDetalleCreditoResponse | None = None

    class Config:
        from_attributes = True


class VentaCreditoResponse(BaseModel):
    id_venta: int
    id_tipo_venta: int
    id_cliente: int
    id_caja_sesion: int
    id_usuario: int
    subtotal: Decimal
    descuento_total: Decimal
    total: Decimal
    fecha: datetime
    estado: str
    tipo_venta_nombre: str | None = None
    detalles: list[DetalleVentaCreditoResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PagoCreditoResponse(BaseModel):
    id_pago_credito: int
    id_metodo_pago: int
    monto_pagado: Decimal
    fecha_pago: datetime
    metodo_pago: MetodoPagoResponse | None = None

    class Config:
        from_attributes = True


class CuentaPorCobrarClienteResponse(BaseModel):
    id_cxc: int
    id_venta: int
    monto_credito: Decimal
    saldo_pendiente: Decimal
    fecha_inicio: datetime
    fecha_vencimiento: datetime
    estado: str
    venta: VentaCreditoResponse
    pagos_credito: list[PagoCreditoResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CobroCuentaPorCobrarResponse(BaseModel):
    id_cxc: int
    id_caja_sesion: int
    monto_credito: Decimal
    saldo_anterior: Decimal
    total_pagado: Decimal
    saldo_pendiente: Decimal
    estado: str
    pagos_credito: list[PagoCreditoResponse]
    movimientos_caja: list[MovimientoCajaResponse]
