from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TipoMovimientoResponse(BaseModel):
    id_tipo_movimiento: int
    nombre: str
    descripcion: str | None
    direccion: str

    model_config = ConfigDict(from_attributes=True)


class ProductoMovimientoResponse(BaseModel):
    id_producto: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class MovimientoInventarioCreate(BaseModel):
    id_producto: int
    id_tipo_movimiento: int
    cantidad: int = Field(gt=0)
    observacion: str | None = None


class ActualizarStockSucursalRequest(BaseModel):
    stock_minimo: int | None = None
    stock_maximo: int | None = None


class MovimientoInventarioResponse(BaseModel):
    id_movimiento: int = Field(validation_alias="id_movimiento_inventario")
    id_movimiento_inventario: int
    id_producto: int
    id_tipo_movimiento: int
    id_usuario: int
    id_sucursal: int | None
    cantidad: int
    observacion: str | None
    fecha_movimiento: datetime
    stock_actual: int
    producto: ProductoMovimientoResponse | None = None
    tipo_movimiento: TipoMovimientoResponse | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True)
