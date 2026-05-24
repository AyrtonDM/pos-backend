from datetime import date

from pydantic import BaseModel, EmailStr

from app.schemas.cliente_schema import ClienteResponse


class SucursalCreate(BaseModel):
    nombre: str
    direccion: str
    telefono: str
    ciudad: str


class SucursalUpdate(BaseModel):
    nombre: str
    direccion: str
    telefono: str
    ciudad: str
    activo: bool


class InvitacionEmpleadoCreate(BaseModel):
    email: EmailStr


class InvitacionClienteCreate(BaseModel):
    email: EmailStr


class PersonaEmpleadoResponse(BaseModel):
    id_persona: int
    nombre_completo: str
    fecha_nacimiento: date
    genero: str
    telefono: str
    documento: str

    class Config:
        from_attributes = True


class UsuarioEmpleadoResponse(BaseModel):
    id_usuario: int
    email: EmailStr
    activo: bool
    persona: PersonaEmpleadoResponse

    class Config:
        from_attributes = True


class EmpleadoSucursalResponse(BaseModel):
    id_usuario_rol: int
    id_usuario: int
    id_rol: int
    id_empresa: int
    id_sucursal: int
    activo: bool
    usuario: UsuarioEmpleadoResponse

    class Config:
        from_attributes = True


class ClienteEmpresaResponse(BaseModel):
    id_usuario_rol: int
    id_usuario: int
    id_rol: int
    id_empresa: int
    id_sucursal: int | None
    activo: bool
    usuario: UsuarioEmpleadoResponse
    cliente: ClienteResponse | None = None

    class Config:
        from_attributes = True


class EmpresaEmpleadoResponse(BaseModel):
    id_empresa: int
    nombre: str
    razon_social: str
    nit: str
    correo: EmailStr
    fecha_creacion: date
    activo: bool

    class Config:
        from_attributes = True


class SucursalEmpleadoResponse(BaseModel):
    id_sucursal: int
    id_empresa: int
    nombre: str
    direccion: str
    telefono: str
    ciudad: str
    fecha_registro: date
    activo: bool

    class Config:
        from_attributes = True


class SucursalEmpleadoAsignadaResponse(BaseModel):
    id_usuario_rol: int
    id_usuario: int
    id_rol: int
    id_empresa: int
    id_sucursal: int
    activo: bool
    empresa: EmpresaEmpleadoResponse
    sucursal: SucursalEmpleadoResponse

    class Config:
        from_attributes = True


class SucursalResponse(BaseModel):
    id_sucursal: int
    id_empresa: int
    nombre: str
    direccion: str
    telefono: str
    ciudad: str
    fecha_registro: date
    activo: bool

    class Config:
        from_attributes = True
