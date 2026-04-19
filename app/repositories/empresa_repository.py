# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.empresas import Empresa
from app.models.usuarios.usuario_rol import UsuarioRol


class EmpresaRepository:
    @staticmethod
    def crear_empresa(db: Session, datos: dict) -> Empresa:
        empresa = Empresa(**datos)
        db.add(empresa)
        db.commit()
        db.refresh(empresa)
        return empresa

    @staticmethod
    def crear_usuario_rol(
        db: Session,
        id_usuario: int,
        id_rol: int,
        id_empresa: int,
        id_sucursal: int | None = None,
        activo: bool = True,
    ) -> UsuarioRol:
        usuario_rol = UsuarioRol(
            id_usuario=id_usuario,
            id_rol=id_rol,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            activo=activo,
        )
        db.add(usuario_rol)
        db.commit()
        db.refresh(usuario_rol)
        return usuario_rol

    @staticmethod
    def obtener_empresas_por_usuario(db: Session, id_usuario: int) -> list[Empresa]:
        return (
            db.query(Empresa)
            .join(UsuarioRol, UsuarioRol.id_empresa == Empresa.id_empresa)
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.activo.is_(True),
            )
            .all()
        )

    @staticmethod
    def obtener_empresa_por_usuario(
        db: Session,
        id_usuario: int,
        id_empresa: int,
    ) -> Empresa | None:
        return (
            db.query(Empresa)
            .join(UsuarioRol, UsuarioRol.id_empresa == Empresa.id_empresa)
            .filter(
                Empresa.id_empresa == id_empresa,
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.activo.is_(True),
            )
            .first()
        )

    @staticmethod
    def actualizar_empresa(empresa: Empresa, datos: dict, db: Session) -> Empresa:
        for campo, valor in datos.items():
            setattr(empresa, campo, valor)

        db.commit()
        db.refresh(empresa)
        return empresa
