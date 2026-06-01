# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.usuarios.rol import Rol

DEFAULT_ROLES = [
    {
        "nombre": "ADMINISTRADOR",
        "tipo": "SISTEMA",
        "descripcion": "ADMINISTRADOR",
        "activo": True,
    },
    {
        "nombre": "CLIENTE",
        "tipo": "SISTEMA",
        "descripcion": "CLIENTE",
        "activo": True,
    },
]


def seed_roles(db: Session) -> None:
    for role_data in DEFAULT_ROLES:
        existe = db.query(Rol).filter(Rol.nombre == role_data["nombre"]).first()
        if not existe:
            db.add(Rol(**role_data))
        elif not existe.tipo:
            existe.tipo = role_data["tipo"]
    db.commit()
