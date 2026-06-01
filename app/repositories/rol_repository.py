from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.usuarios.permiso import Permiso
from app.models.usuarios.rol import Rol
from app.models.usuarios.rol_permiso import RolPermiso


class RolRepository:
    @staticmethod
    def crear_rol(db: Session, datos: dict) -> Rol:
        rol = Rol(**datos)
        db.add(rol)
        db.flush()
        db.refresh(rol)
        return rol

    @staticmethod
    def obtener_roles(db: Session, id_empresa: int) -> list[Rol]:
        return (
            db.query(Rol)
            .filter(
                Rol.activo.is_(True),
                (
                    (Rol.id_empresa.is_(None))
                    | (Rol.tipo == "SISTEMA")
                    | (Rol.id_empresa == id_empresa)
                ),
            )
            .order_by(Rol.id_rol.asc())
            .all()
        )

    @staticmethod
    def obtener_rol_por_id(db: Session, id_rol: int) -> Rol | None:
        return (
            db.query(Rol)
            .options(joinedload(Rol.roles_permisos))
            .filter(Rol.id_rol == id_rol)
            .first()
        )

    @staticmethod
    def obtener_permiso_por_id(db: Session, id_permiso: int) -> Permiso | None:
        return db.query(Permiso).filter(Permiso.id_permiso == id_permiso).first()

    @staticmethod
    def crear_rol_permiso(db: Session, id_rol: int, id_permiso: int) -> RolPermiso:
        rol_permiso = RolPermiso(id_rol=id_rol, id_permiso=id_permiso, activo=True)
        db.add(rol_permiso)
        db.flush()
        db.refresh(rol_permiso)
        return rol_permiso