# -*- coding: utf-8 -*-
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from sqlalchemy.orm import joinedload
from app.models.empresas import Empresa
from app.models.empresas.historial_suscripcion import HistorialSuscripcion

from app.models.usuarios import Usuario
from app.models.usuarios.modulo import Modulo
from app.models.usuarios.permiso import Permiso
from app.models.usuarios.rol import Rol
from app.models.usuarios.rol_permiso import RolPermiso
from app.models.usuarios.usuario_rol import UsuarioRol


class EmpresaRepository:
    @staticmethod
    def crear_empresa(db: Session, datos: dict) -> Empresa:
        empresa = Empresa(**datos)
        db.add(empresa)
        db.flush()
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
        db.flush()
        db.refresh(usuario_rol)
        return usuario_rol

    @staticmethod
    def obtener_rol_por_nombre(db: Session, nombre: str) -> Rol | None:
        return db.query(Rol).filter(Rol.nombre == nombre).first()

    @staticmethod
    def obtener_usuario_rol_activo_distinto_cliente(
        db: Session,
        id_usuario: int,
        id_empresa: int,
    ) -> UsuarioRol | None:
        return (
            db.query(UsuarioRol)
            .options(joinedload(UsuarioRol.rol))
            .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.activo.is_(True),
                Rol.nombre != "CLIENTE",
            )
            .order_by(UsuarioRol.id_usuario_rol.asc())
            .first()
        )

    @staticmethod
    def obtener_permisos_por_rol(db: Session, id_rol: int) -> list[tuple[Permiso, bool]]:
        return (
            db.query(Permiso, RolPermiso.activo)
            .join(RolPermiso, RolPermiso.id_permiso == Permiso.id_permiso)
            .options(joinedload(Permiso.modulo))
            .filter(RolPermiso.id_rol == id_rol)
            .order_by(Permiso.id_permiso.asc())
            .all()
        )

    @staticmethod
    def obtener_permisos_agrupados_por_modulo(db: Session) -> list[Modulo]:
        return (
            db.query(Modulo)
            .options(joinedload(Modulo.permisos))
            .order_by(Modulo.id_modulo.asc())
            .all()
        )

    @staticmethod
    def obtener_empresa_por_id(db: Session, id_empresa: int) -> Empresa | None:
        return db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()

    @staticmethod
    def obtener_usuario_rol_sin_sucursal(
        db: Session,
        id_usuario: int,
        id_empresa: int,
    ) -> UsuarioRol | None:
        return (
            db.query(UsuarioRol)
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.id_sucursal.is_(None),
                UsuarioRol.activo.is_(True),
            )
            .first()
        )

    @staticmethod
    def obtener_usuario_rol_activo(
        db: Session,
        id_usuario: int,
        id_empresa: int,
    ) -> UsuarioRol | None:
        return (
            db.query(UsuarioRol)
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.activo.is_(True),
            )
            .first()
        )

    @staticmethod
    def obtener_usuarios_rol_por_empresa(
        db: Session,
        id_usuario: int,
        id_empresa: int,
    ) -> list[UsuarioRol]:
        return (
            db.query(UsuarioRol)
            .options(joinedload(UsuarioRol.usuario).joinedload(Usuario.persona))
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_empresa == id_empresa,
            )
            .all()
        )

    def obtener_usuario_rol_por_sucursal_y_rol(
        db: Session,
        id_usuario: int,
        id_empresa: int,
        id_sucursal: int,
        id_rol: int,
    ) -> UsuarioRol | None:
        return (
            db.query(UsuarioRol)
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.id_sucursal == id_sucursal,
                UsuarioRol.id_rol == id_rol,
                UsuarioRol.activo.is_(True),
            )
            .first()
        )

    @staticmethod
    def obtener_usuario_rol_por_empresa_y_rol_sin_sucursal(
        db: Session,
        id_usuario: int,
        id_empresa: int,
        id_rol: int,
    ) -> UsuarioRol | None:
        return (
            db.query(UsuarioRol)
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.id_rol == id_rol,
                UsuarioRol.id_sucursal.is_(None),
                UsuarioRol.activo.is_(True),
            )
            .first()
        )

    @staticmethod
    def obtener_usuarios_rol_por_sucursal_y_rol(
        db: Session,
        id_empresa: int,
        id_sucursal: int,
        id_rol: int,
    ) -> list[UsuarioRol]:
        return (
            db.query(UsuarioRol)
            .options(joinedload(UsuarioRol.usuario).joinedload(Usuario.persona))
            .filter(
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.id_sucursal == id_sucursal,
                UsuarioRol.id_rol == id_rol,
                UsuarioRol.activo.is_(True),
            )
            .all()
        )

    @staticmethod
    def obtener_personal_por_empresa_excluyendo_roles(
        db: Session,
        id_empresa: int,
        roles_excluidos: list[str],
    ) -> list[UsuarioRol]:
        return (
            db.query(UsuarioRol)
            .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
            .options(joinedload(UsuarioRol.usuario).joinedload(Usuario.persona))
            .filter(
                UsuarioRol.id_empresa == id_empresa,
                Rol.nombre.notin_(roles_excluidos),
            )
            .order_by(
                UsuarioRol.id_usuario.asc(),
                UsuarioRol.id_sucursal.asc(),
                UsuarioRol.id_usuario_rol.asc(),
            )
            .all()
        )

    @staticmethod
    def contar_usuarios_activos_por_empresa_excluyendo_roles(
        db: Session,
        id_empresa: int,
        roles_excluidos: list[str],
    ) -> int:
        return (
            db.query(func.count(func.distinct(UsuarioRol.id_usuario)))
            .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
            .filter(
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.activo.is_(True),
                Rol.nombre.notin_(roles_excluidos),
            )
            .scalar()
            or 0
        )

    @staticmethod
    def obtener_usuarios_rol_por_empresa_y_rol_sin_sucursal(
        db: Session,
        id_empresa: int,
        id_rol: int,
    ) -> list[UsuarioRol]:
        return (
            db.query(UsuarioRol)
            .options(joinedload(UsuarioRol.usuario).joinedload(Usuario.persona))
            .filter(
                UsuarioRol.id_empresa == id_empresa,
                UsuarioRol.id_rol == id_rol,
                UsuarioRol.id_sucursal.is_(None),
                UsuarioRol.activo.is_(True),
            )
            .all()
        )

    @staticmethod
    def obtener_sucursales_empleado_por_usuario(
        db: Session,
        id_usuario: int,
        id_rol: int,
        id_empresa: int | None = None,
    ) -> list[UsuarioRol]:
        query = (
            db.query(UsuarioRol)
            .options(
                joinedload(UsuarioRol.empresa),
                joinedload(UsuarioRol.sucursal),
            )
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_rol == id_rol,
                UsuarioRol.id_sucursal.is_not(None),
                UsuarioRol.activo.is_(True),
            )
        )

        if id_empresa is not None:
            query = query.filter(UsuarioRol.id_empresa == id_empresa)

        return query.all()

    @staticmethod
    def asignar_sucursal_a_usuario_rol(
        db: Session,
        usuario_rol: UsuarioRol,
        id_sucursal: int,
    ) -> UsuarioRol:
        usuario_rol.id_sucursal = id_sucursal
        db.flush()
        db.refresh(usuario_rol)
        return usuario_rol

    @staticmethod
    def obtener_empresas_por_usuario(db: Session, id_usuario: int) -> list[Empresa]:
        return (
            db.query(Empresa)
            .join(UsuarioRol, UsuarioRol.id_empresa == Empresa.id_empresa)
            .options(joinedload(Empresa.historial_suscripciones).joinedload(HistorialSuscripcion.plan))
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.activo.is_(True),
            )
            .all()
        )

    @staticmethod
    def obtener_empresas_por_usuario_y_rol(
        db: Session,
        id_usuario: int,
        id_rol: int,
    ) -> list[Empresa]:
        return (
            db.query(Empresa)
            .join(UsuarioRol, UsuarioRol.id_empresa == Empresa.id_empresa)
            .options(joinedload(Empresa.historial_suscripciones).joinedload(HistorialSuscripcion.plan))
            .filter(
                UsuarioRol.id_usuario == id_usuario,
                UsuarioRol.id_rol == id_rol,
                UsuarioRol.activo.is_(True),
            )
            .distinct()
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
            .options(joinedload(Empresa.historial_suscripciones).joinedload(HistorialSuscripcion.plan))
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
