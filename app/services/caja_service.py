# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuarios import Usuario
from app.repositories.caja_repository import CajaRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.sucursal_repository import SucursalRepository


class CajaService:
    @staticmethod
    def _validar_usuario_activo(current_user: Usuario) -> None:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

    @staticmethod
    def _validar_empresa_del_usuario(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ) -> None:
        CajaService._validar_usuario_activo(current_user)

        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

    @staticmethod
    def _obtener_sucursal_validada(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ):
        CajaService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )

        sucursal = SucursalRepository.obtener_sucursal_por_empresa(
            db=db,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
        if sucursal is None:
            raise LookupError("Sucursal no encontrada para esta empresa.")

        return sucursal

    @staticmethod
    def _obtener_caja_validada(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        id_caja: int,
    ):
        CajaService._obtener_sucursal_validada(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )

        caja = CajaRepository.obtener_caja_por_sucursal(
            db=db,
            id_sucursal=id_sucursal,
            id_caja=id_caja,
        )
        if caja is None:
            raise LookupError("Caja no encontrada para esta sucursal.")

        return caja

    @staticmethod
    def crear_caja(
        db: Session,
        current_user: Usuario,
        id_sucursal: int,
        nombre: str,
        codigo: str,
    ):
        CajaService._validar_usuario_activo(current_user)

        sucursal = SucursalRepository.obtener_sucursal_por_id(
            db=db,
            id_sucursal=id_sucursal,
        )
        if sucursal is None:
            raise LookupError("Sucursal no encontrada.")

        CajaService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=sucursal.id_empresa,
        )

        try:
            caja = CajaRepository.crear_caja(
                db=db,
                datos={
                    "id_sucursal": id_sucursal,
                    "nombre": nombre,
                    "codigo": codigo,
                    "fecha_creacion": date.today(),
                    "activo": True,
                },
            )
            db.commit()
            db.refresh(caja)
            return caja
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo crear la caja.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def listar_cajas_de_sucursal(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ):
        CajaService._obtener_sucursal_validada(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )

        return CajaRepository.obtener_cajas_por_sucursal(
            db=db,
            id_sucursal=id_sucursal,
        )

    @staticmethod
    def obtener_caja(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        id_caja: int,
    ):
        return CajaService._obtener_caja_validada(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_caja=id_caja,
        )

    @staticmethod
    def actualizar_caja(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
        id_caja: int,
        nombre: str,
        codigo: str,
        activo: bool,
    ):
        caja = CajaService._obtener_caja_validada(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_caja=id_caja,
        )

        return CajaRepository.actualizar_caja(
            db=db,
            caja=caja,
            datos={
                "nombre": nombre,
                "codigo": codigo,
                "activo": activo,
            },
        )

    @staticmethod
    def crear_caja_sesion(
        db: Session,
        current_user: Usuario,
        id_caja: int,
        monto_inicial: Decimal,
        nota: str | None,
    ):
        CajaService._validar_usuario_activo(current_user)

        caja = CajaRepository.obtener_caja_por_id(db=db, id_caja=id_caja)
        if caja is None:
            raise LookupError("Caja no encontrada.")

        CajaService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=caja.sucursal.id_empresa,
        )

        try:
            caja_sesion = CajaRepository.crear_caja_sesion(
                db=db,
                datos={
                    "id_caja": id_caja,
                    "fecha_apertura": datetime.utcnow(),
                    "fecha_cierre": None,
                    "monto_inicial": monto_inicial,
                    "monto_final": None,
                    "estado": "Abierto",
                    "nota": nota,
                },
            )
            db.commit()
            db.refresh(caja_sesion)
            return caja_sesion
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo crear la sesion de caja.") from exc
        except Exception:
            db.rollback()
            raise
