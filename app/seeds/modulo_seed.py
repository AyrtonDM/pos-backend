# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.usuarios.modulo import Modulo


DEFAULT_MODULOS = [
    {"codigo": "USUARIOS", "nombre": "Gestion de Usuarios"},
    {"codigo": "EMPRESAS", "nombre": "Gestion de Empresas"},
    {"codigo": "INVENTARIO", "nombre": "Gestion de Productos e Inventario"},
    {"codigo": "VENTAS", "nombre": "Gestion de Ventas"},
    {"codigo": "CLIENTES", "nombre": "Gestion de Clientes"},
    {"codigo": "CAJAS", "nombre": "Gestion de Cajas"},
    {"codigo": "REPORTES", "nombre": "Gestion de Reportes"},
]


def seed_modulos(db: Session) -> None:
    for modulo_data in DEFAULT_MODULOS:
        existe = db.query(Modulo).filter(Modulo.codigo == modulo_data["codigo"]).first()
        if not existe:
            db.add(Modulo(**modulo_data))
    db.commit()
