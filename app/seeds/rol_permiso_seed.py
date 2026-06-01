# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.usuarios.permiso import Permiso
from app.models.usuarios.rol import Rol
from app.models.usuarios.rol_permiso import RolPermiso


def seed_rol_permisos_admin(db: Session) -> None:
    rol_admin = db.query(Rol).filter(Rol.nombre == "ADMINISTRADOR").first()
    if rol_admin is None:
        return

    permisos = db.query(Permiso).all()
    for permiso in permisos:
        existe = (
            db.query(RolPermiso)
            .filter(
                RolPermiso.id_rol == rol_admin.id_rol,
                RolPermiso.id_permiso == permiso.id_permiso,
            )
            .first()
        )
        if not existe:
            db.add(
                RolPermiso(
                    id_rol=rol_admin.id_rol,
                    id_permiso=permiso.id_permiso,
                    activo=True,
                )
            )
        elif not existe.activo:
            existe.activo = True

    db.commit()
