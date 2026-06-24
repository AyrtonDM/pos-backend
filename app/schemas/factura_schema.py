from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class FacturaDetalleResponse(BaseModel):
    id_detalle_venta: int
    id_producto: int
    producto: str
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    subtotal: Decimal
    total: Decimal
    descripcion: str | None = None


class FacturaVentaResponse(BaseModel):
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
    detalles: list[FacturaDetalleResponse]


class FacturaListadoResponse(BaseModel):
    id_factura: int
    id_venta: int
    nit_emisor: str
    numero_factura: int
    fecha_emision: datetime
    nit_cliente: str
    nombre_cliente: str
    monto_total: Decimal
    iva: Decimal
    cufd: str
    cuf: str
    xml_generado: str
    pdf_generado: str
    venta: FacturaVentaResponse


class ReenviarFacturaRequest(BaseModel):
    id_factura: int = Field(gt=0)


class ReenviarFacturaResponse(BaseModel):
    mensaje: str
    id_factura: int
    correo_cliente: str
    enviado: bool
