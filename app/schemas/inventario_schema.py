from datetime import datetime

from pydantic import BaseModel, Field


class TipoMovimientoResponse(BaseModel):
    id_tipo_movimiento: int
    nombre: str
    descripcion: str | None
    direccion: str

    class Config:
        from_attributes = True


class MovimientoInventarioCreate(BaseModel):
    id_producto: int
    id_tipo_movimiento: int
    cantidad: int = Field(gt=0)
    observacion: str | None = None


class MovimientoInventarioResponse(BaseModel):
    id_movimiento_inventario: int
    id_producto: int
    id_tipo_movimiento: int
    id_usuario: int
    id_sucursal: int | None
    cantidad: int
    observacion: str | None
    fecha_movimiento: datetime
    stock_actual: int
    tipo_movimiento: TipoMovimientoResponse | None

    class Config:
        from_attributes = True


class StockProductoResponse(BaseModel):
    id_stock: int
    id_producto: int
    id_sucursal: int
    cantidad: int
    stock_minimo: int | None
    stock_maximo: int | None
    fecha_actualizacion: datetime
    nombre_producto: str
    unidad_medida: str
    precio: float
    imagen: str | None
    activo: bool

    class Config:
        from_attributes = True


class StockUpdateRequest(BaseModel):
    stock_minimo: int
    stock_maximo: int

    class Config:
        from_attributes = True


ActualizarStockSucursalRequest = StockUpdateRequest


class MovimientoProductoSimple(BaseModel):
    id_producto: int
    nombre: str


class TipoMovimientoSimple(BaseModel):
    id_tipo_movimiento: int
    nombre: str


class MovimientoListResponse(BaseModel):
    id_movimiento: int
    id_producto: int
    cantidad: int
    observacion: str | None
    tipo: str
    producto: MovimientoProductoSimple
    tipo_movimiento: TipoMovimientoSimple

    class Config:
        from_attributes = True
