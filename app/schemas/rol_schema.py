from pydantic import BaseModel, Field


class RolCreateRequest(BaseModel):
    nombre: str
    permiso_ids: list[int] = Field(..., min_length=1)


class RolUpdateRequest(BaseModel):
    activo: bool
    permiso_ids: list[int] = Field(default_factory=list)


class RolResponse(BaseModel):
    id_rol: int
    nombre: str
    id_empresa: int | None = None
    tipo: str | None = None
    descripcion: str
    activo: bool

    class Config:
        from_attributes = True


class RolPermisoResponse(BaseModel):
    id_rol_permiso: int
    id_rol: int
    id_permiso: int
    activo: bool

    class Config:
        from_attributes = True


class RolDetalleResponse(RolResponse):
    rol_permisos: list[RolPermisoResponse]


class RolCreateResponse(BaseModel):
    rol: RolResponse
    permiso_ids: list[int]