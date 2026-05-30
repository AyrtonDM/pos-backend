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
    id_empresa: int | None
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


class CategoriaProductoConSubcategoriasResponse(BaseModel):
    id_categoria_producto: int
    id_empresa: int | None
    nombre: str
    descripcion: str | None
    activo: bool
    subcategorias: list[SubcategoriaProductoResponse]

    class Config:
        from_attributes = True


class ProductoBase(BaseModel):
    id_subcategoria: int
    nombre: str = Field(max_length=150)
    codigo_barra: str | None = Field(default=None, max_length=100)
    descripcion: str | None = None
    unidad_medida: str = Field(max_length=50)
    precio: Decimal = Decimal("0")
    activo: bool = True


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    id_subcategoria: int | None = None
    nombre: str | None = None
    codigo_barra: str | None = None
    descripcion: str | None = None
    unidad_medida: str | None = None
    precio: Decimal | None = None
    activo: bool | None = None


class ProductoResponse(BaseModel):
    id_producto: int
    id_empresa: int | None
    id_subcategoria: int | None
    nombre: str
    codigo_barra: str | None
    descripcion: str | None
    unidad_medida: str
    precio: Decimal
    imagen: str | None
    activo: bool
    subcategoria: SubcategoriaProductoResponse | None

    class Config:
        from_attributes = True
