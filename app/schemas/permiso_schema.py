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


class PlanModuloResponse(BaseModel):
    id_plan_modulo: int
    id_plan: int
    id_modulo: int
    configuracion: str | None = None
    modulo: ModuloResponse | None = None

    class Config:
        from_attributes = True


class PlanConModulosResponse(BaseModel):
    id_plan: int
    nombre: str
    descripcion: str
    precio: float
    plan_modulos: list[PlanModuloResponse]


class SuscripcionActivaResponse(BaseModel):
    id_historial_suscripcion: int
    id_empresa: int
    id_plan: int
    fecha_inicio: str
    fecha_fin: str | None
    estado: str
    plan: PlanConModulosResponse


class MisPermisosEmpresaResponse(BaseModel):
    permisos: list[PermisoConRolPermisoResponse]
    suscripcion_activa: SuscripcionActivaResponse | None
