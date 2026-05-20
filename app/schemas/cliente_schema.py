# -*- coding: utf-8 -*-
from decimal import Decimal

from pydantic import BaseModel, Field


class CategoriaClienteBase(BaseModel):
    nombre: str = Field(max_length=150)
    descripcion: str | None = None
    permite_credito: bool = True
    descuento_base: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    limite_credito: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    activo: bool = True


class CategoriaClienteCreate(CategoriaClienteBase):
    pass


class CategoriaClienteUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    permite_credito: bool | None = None
    descuento_base: Decimal | None = None
    limite_credito: Decimal | None = None
    activo: bool | None = None


class CategoriaClienteResponse(BaseModel):
    id_categoria_cliente: int
    id_empresa: int
    nombre: str
    descripcion: str | None
    permite_credito: bool
    descuento_base: Decimal
    limite_credito: Decimal
    activo: bool

    class Config:
        from_attributes = True


class ClienteBase(BaseModel):
    id_categoria_cliente: int
    codigo_cliente: str = Field(max_length=50)
    saldo_credito: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    limite_credito: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    activo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    id_categoria_cliente: int | None = None
    codigo_cliente: str | None = None
    saldo_credito: Decimal | None = None
    limite_credito: Decimal | None = None
    activo: bool | None = None


class ClienteResponse(BaseModel):
    id_cliente: int
    id_empresa: int
    id_categoria_cliente: int
    codigo_cliente: str
    saldo_credito: Decimal
    limite_credito: Decimal
    activo: bool

    class Config:
        from_attributes = True
