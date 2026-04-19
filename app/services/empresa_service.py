# -*- coding: utf-8 -*-
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.empresa_repository import EmpresaRepository
from app.models.usuarios import Usuario


class EmpresaService:
    @staticmethod
    def crear_empresa_para_usuario(
        db: Session,
        current_user: Usuario,
        nombre: str,
        razon_social: str,
        nit: str,
        correo: str,
    ) -> dict:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

        rol_administrador = EmpresaRepository.obtener_rol_por_nombre(
            db=db,
            nombre="ADMINISTRADOR",
        )
        if rol_administrador is None:
            raise ValueError("No existe el rol ADMINISTRADOR.")

        try:
            empresa = EmpresaRepository.crear_empresa(
                db=db,
                datos={
                    "nombre": nombre,
                    "razon_social": razon_social,
                    "nit": nit,
                    "correo": correo,
                    "fecha_creacion": date.today(),
                    "activo": True,
                },
            )

            usuario_rol = EmpresaRepository.crear_usuario_rol(
                db=db,
                id_usuario=current_user.id_usuario,
                id_rol=rol_administrador.id_rol,
                id_empresa=empresa.id_empresa,
                activo=True,
            )

            db.commit()
            db.refresh(empresa)
            db.refresh(usuario_rol)
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Ya existe una empresa con ese NIT o correo.") from exc
        except Exception:
            db.rollback()
            raise

        return {
            "empresa": {
                "id_empresa": empresa.id_empresa,
                "nombre": empresa.nombre,
                "razon_social": empresa.razon_social,
                "nit": empresa.nit,
                "correo": empresa.correo,
                "fecha_creacion": empresa.fecha_creacion,
                "activo": empresa.activo,
            },
            "usuario_rol": {
                "id_usuario_rol": usuario_rol.id_usuario_rol,
                "id_usuario": usuario_rol.id_usuario,
                "id_rol": usuario_rol.id_rol,
                "id_empresa": usuario_rol.id_empresa,
                "id_sucursal": usuario_rol.id_sucursal,
                "activo": usuario_rol.activo,
            },
        }

    @staticmethod
    def obtener_empresas_del_usuario(db: Session, current_user: Usuario):
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

        return EmpresaRepository.obtener_empresas_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
        )

    @staticmethod
    def obtener_empresa_del_usuario(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ):
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

        return empresa

    @staticmethod
    def actualizar_empresa_del_usuario(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        nombre: str,
        razon_social: str,
        nit: str,
        correo: str,
        activo: bool,
    ):
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

        return EmpresaRepository.actualizar_empresa(
            db=db,
            empresa=empresa,
            datos={
                "nombre": nombre,
                "razon_social": razon_social,
                "nit": nit,
                "correo": correo,
                "activo": activo,
            },
        )
