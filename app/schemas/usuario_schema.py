from datetime import date

from pydantic import BaseModel, EmailStr


class PersonaCreate(BaseModel):
    nombre_completo: str
    fecha_nacimiento: date
    genero: str
    telefono: str
    documento: str


class UsuarioRegister(BaseModel):
    email: EmailStr
    contrasena: str
    nombre_completo: str
    fecha_nacimiento: date
    genero: str
    telefono: str
    documento: str


class UsuarioVerifyCode(BaseModel):
    email: EmailStr
    codigo: str


class UsuarioResponse(BaseModel):
    id_usuario: int
    email: str
    activo: bool

    class Config:
        from_attributes = True
