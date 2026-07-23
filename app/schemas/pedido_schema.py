from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List


class PedidoClienteDetalleCreate(BaseModel):
    id_producto: int
    cantidad: int
    precio_unitario_estimado: Decimal = Decimal("0.00")


class PedidoClienteCreate(BaseModel):
    id_sucursal: int
    observacion_cliente: str | None = None
    detalles: List[PedidoClienteDetalleCreate]


class PedidoClienteEstadoUpdate(BaseModel):
    estado: str
    observacion_empresa: str | None = None


class PedidoClienteDetalleResponse(BaseModel):
    id_detalle: int
    id_pedido: int
    id_producto: int
    cantidad: int
    precio_unitario_estimado: Decimal
    descuento_estimado: Decimal
    subtotal_estimado: Decimal

    class Config:
        from_attributes = True


class PedidoClienteResponse(BaseModel):
    id_pedido: int
    id_empresa: int
    id_sucursal: int
    id_cliente: int
    id_venta: int | None
    estado: str
    subtotal_estimado: Decimal
    descuento_estimado: Decimal
    total_estimado: Decimal
    observacion_cliente: str | None
    observacion_empresa: str | None
    fecha_creacion: datetime
    fecha_confirmacion: datetime | None
    fecha_preparacion: datetime | None
    fecha_listo: datetime | None
    fecha_cancelacion: datetime | None
    detalles: List[PedidoClienteDetalleResponse]

    class Config:
        from_attributes = True
