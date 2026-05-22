# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuarios import Usuario
from app.models.ventas import MetodoPago
from app.repositories.caja_repository import CajaRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.sucursal_repository import SucursalRepository
from app.repositories.movimiento_caja_repository import MovimientoCajaRepository
from app.models.empresas import TipoMovimientoCaja


class CajaSesionAbiertaError(Exception):
    def __init__(self, id_caja: int, id_caja_sesion: int, message: str):
        self.id_caja = id_caja
        self.id_caja_sesion = id_caja_sesion
        self.message = message
        super().__init__(message)


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

        sesion_abierta_usuario = CajaRepository.obtener_sesion_abierta_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
        )
        if sesion_abierta_usuario is not None:
            raise CajaSesionAbiertaError(
                id_caja=sesion_abierta_usuario.id_caja,
                id_caja_sesion=sesion_abierta_usuario.id_caja_sesion,
                message="Tienes una sesion abierta aun",
            )

        sesion_abierta_caja = CajaRepository.obtener_sesion_abierta_por_caja(
            db=db,
            id_caja=id_caja,
        )
        if sesion_abierta_caja is not None:
            raise CajaSesionAbiertaError(
                id_caja=id_caja,
                id_caja_sesion=sesion_abierta_caja.id_caja_sesion,
                message="Esta caja tiene ya una sesion abierta",
            )

        try:
            caja_sesion = CajaRepository.crear_caja_sesion(
                db=db,
                datos={
                    "id_caja": id_caja,
                    "id_usuario": current_user.id_usuario,
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

    @staticmethod
    def crear_movimiento_caja(
        db: Session,
        current_user: Usuario,
        id_caja_sesion: int,
        concepto: str | None,
        monto,
        id_tipo_movimiento_caja: int,
        id_metodo_pago: int | None,
    ):
        CajaService._validar_usuario_activo(current_user)

        caja_sesion = CajaRepository.obtener_caja_sesion_por_id(
            db=db, id_caja_sesion=id_caja_sesion
        )
        if caja_sesion is None:
            raise LookupError("Sesion de caja no encontrada.")

        # validar que la sesion pertenece a la empresa del usuario
        CajaService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=caja_sesion.caja.sucursal.id_empresa,
        )

        tipo = db.query(TipoMovimientoCaja).filter(
            TipoMovimientoCaja.id_tipo_movimiento_caja == id_tipo_movimiento_caja
        ).first()
        if tipo is None:
            raise LookupError("Tipo de movimiento de caja no encontrado.")

        if id_metodo_pago is not None:
            metodo_pago = db.query(MetodoPago).filter(
                MetodoPago.id_metodo_pago == id_metodo_pago
            ).first()
            if metodo_pago is None:
                raise LookupError("Metodo de pago no encontrado.")

        try:
            movimiento = MovimientoCajaRepository.crear_movimiento(
                db=db,
                datos={
                    "id_metodo_pago": id_metodo_pago,
                    "id_tipo_movimiento_caja": id_tipo_movimiento_caja,
                    "id_caja_sesion": id_caja_sesion,
                    "id_usuario": current_user.id_usuario,
                    "fecha": datetime.utcnow(),
                    "monto": monto,
                    "concepto": concepto,
                },
            )
            db.commit()
            db.refresh(movimiento)
            return movimiento
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo registrar el movimiento de caja.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def listar_movimientos_de_caja_sesion(
        db: Session,
        current_user: Usuario,
        id_caja_sesion: int,
    ):
        CajaService._validar_usuario_activo(current_user)

        caja_sesion = CajaRepository.obtener_caja_sesion_por_id(
            db=db,
            id_caja_sesion=id_caja_sesion,
        )
        if caja_sesion is None:
            raise LookupError("Sesion de caja no encontrada.")

        CajaService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=caja_sesion.caja.sucursal.id_empresa,
        )

        return CajaRepository.obtener_movimientos_por_caja_sesion(
            db=db,
            id_caja_sesion=id_caja_sesion,
        )
