from pydantic import BaseModel


class ModuloResponse(BaseModel):
    id_modulo: int
    codigo: str
    nombre: str

    class Config:
        from_attributes = True


class PermisoResponse(BaseModel):
    id_permiso: int
    codigo: str
    nombre: str
    id_modulo: int
    modulo: ModuloResponse | None = None

    class Config:
        from_attributes = True


class PermisoConRolPermisoResponse(PermisoResponse):
    activo_rol_permiso: bool


class PermisoSimpleResponse(BaseModel):
    id_permiso: int
    codigo: str
    nombre: str

    class Config:
        from_attributes = True


class PermisosPorModuloResponse(ModuloResponse):
    permisos: list[PermisoSimpleResponse]
