from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CategoriaProductoBase(BaseModel):
    nombre: str = Field(max_length=150)
    descripcion: str | None = None
    activo: bool = True


class CategoriaProductoCreate(CategoriaProductoBase):
    pass


class CategoriaProductoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class CategoriaProductoResponse(BaseModel):
    id_categoria_producto: int
    nombre: str
    descripcion: str | None
    activo: bool

    class Config:
        from_attributes = True


class SubcategoriaProductoBase(BaseModel):
    id_categoria_producto: int
    nombre: str = Field(max_length=150)
    descripcion: str | None = None
    activo: bool = True


class SubcategoriaProductoCreate(SubcategoriaProductoBase):
    pass


class SubcategoriaProductoUpdate(BaseModel):
    id_categoria_producto: int | None = None
    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class SubcategoriaProductoResponse(BaseModel):
    id_subcategoria: int
    id_categoria_producto: int
    nombre: str
    descripcion: str | None
    activo: bool

    class Config:
        from_attributes = True


class StockBase(BaseModel):
    cantidad: int = Field(ge=0)
    stock_min: int = Field(ge=0)
    stock_max: int = Field(ge=0)


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    cantidad: int | None = Field(default=None, ge=0)
    stock_min: int | None = Field(default=None, ge=0)
    stock_max: int | None = Field(default=None, ge=0)


class StockResponse(BaseModel):
    id_stock: int
    cantidad: int
    stock_min: int
    stock_max: int
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class ProductoBase(BaseModel):
    id_empresa: int
    id_subcategoria: int
    nombre: str = Field(max_length=150)
    costo: Decimal = Decimal("0")
    precio: Decimal = Decimal("0")
    stock: StockCreate


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    id_empresa: int | None = None
    id_subcategoria: int | None = None
    nombre: str | None = None
    costo: Decimal | None = None
    precio: Decimal | None = None
    stock: StockUpdate | None = None


class ProductoResponse(BaseModel):
    id_producto: int
    id_empresa: int
    id_subcategoria: int
    nombre: str
    costo: Decimal
    precio: Decimal
    imagen: str | None
    subcategoria: SubcategoriaProductoResponse
    stock: StockResponse

    class Config:
        from_attributes = True