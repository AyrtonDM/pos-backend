from datetime import date

from pydantic import BaseModel, EmailStr


class EmpresaCreate(BaseModel):
    nombre: str
    razon_social: str
    nit: str
    correo: EmailStr


class EmpresaUpdate(BaseModel):
    nombre: str
    razon_social: str
    nit: str
    correo: EmailStr
    activo: bool


class EmpresaResponse(BaseModel):
    id_empresa: int
    nombre: str
    razon_social: str
    nit: str
    correo: EmailStr
    fecha_creacion: date
    activo: bool

    class Config:
        from_attributes = True
