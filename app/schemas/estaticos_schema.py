from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class CajaResumen(BaseModel):
    id_sucursal: int
    id_caja: int
    monto_inicial: float
    total_ingresos: float
    total_egresos: float
    diferencia: float


class MovimientoCajaItem(BaseModel):
    id_movimiento_caja: int
    id_caja_sesion: int
    id_caja: int
    fecha: datetime
    monto: float
    concepto: Optional[str]
    tipo_movimiento: Optional[str]


class InventarioResumenItem(BaseModel):
    id_producto: int
    nombre_producto: str
    total_stock: int


class MovimientoInventarioItem(BaseModel):
    id_movimiento_inventario: int
    id_producto: int
    cantidad: int
    fecha_movimiento: datetime
    observacion: Optional[str]


class VentaResumen(BaseModel):
    id_sucursal: int
    total_ventas: float
    cantidad_ventas: int


class VentaDetalleItem(BaseModel):
    id_venta: int
    fecha: datetime
    total: float
    id_caja_sesion: int
    id_usuario: int
