# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuarios import Usuario
from app.models.empresas import CajaCierreDetalle
from app.models.empresas import MovimientoCaja
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
    def _signo_tipo_movimiento_caja(nombre_tipo: str | None) -> Decimal:
        nombre = (nombre_tipo or "").strip().upper()
        if nombre in {"EGRESO", "AJUSTE_NEGATIVO"}:
            return Decimal("-1")
        if nombre == "CIERRE":
            return Decimal("0")
        return Decimal("1")

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
            metodo_efectivo = (
                db.query(MetodoPago)
                .filter(MetodoPago.nombre == "EFECTIVO")
                .first()
            )
            if metodo_efectivo is None:
                raise LookupError("Metodo de pago EFECTIVO no encontrado.")

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

            # Crear movimiento de caja tipo APERTURA con el mismo monto inicial.
            # Se hace de forma independiente para no cambiar la respuesta del endpoint.
            try:
                movimiento = MovimientoCajaRepository.crear_movimiento(
                    db=db,
                    datos={
                        "id_metodo_pago": metodo_efectivo.id_metodo_pago,
                        "id_tipo_movimiento_caja": 1,  # APERTURA (seed por defecto)
                        "id_caja_sesion": caja_sesion.id_caja_sesion,
                        "id_usuario": current_user.id_usuario,
                        "fecha": datetime.utcnow(),
                        "monto": monto_inicial,
                        "concepto": f"APERTURA {caja_sesion.id_caja_sesion}",
                    },
                )
                db.commit()
                db.refresh(movimiento)
            except Exception:
                # No interrumpir la creación de la sesión si falla el movimiento de apertura.
                db.rollback()

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

    @staticmethod
    def resumen_movimientos_por_metodo_pago(
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

        movimientos = CajaRepository.obtener_movimientos_por_caja_sesion(
            db=db,
            id_caja_sesion=id_caja_sesion,
        )

        grupos: dict[int | None, dict] = {}
        monto_esperado_total = Decimal("0.00")

        for movimiento in movimientos:
            signo = CajaService._signo_tipo_movimiento_caja(
                movimiento.tipo_movimiento_caja.nombre if movimiento.tipo_movimiento_caja else None
            )
            monto_base = Decimal(movimiento.monto or 0)
            monto_ajustado = monto_base * signo

            monto_esperado_total += monto_ajustado

            grupo = grupos.setdefault(
                movimiento.id_metodo_pago,
                {
                    "id_metodo_pago": movimiento.id_metodo_pago,
                    "metodo_pago": movimiento.metodo_pago.nombre if movimiento.metodo_pago else None,
                    "total_ingresos": Decimal("0.00"),
                    "total_egresos": Decimal("0.00"),
                    "monto_esperado": Decimal("0.00"),
                    "movimientos": [],
                },
            )
            grupo["movimientos"].append(movimiento)
            grupo["monto_esperado"] += monto_ajustado
            if monto_ajustado >= 0:
                grupo["total_ingresos"] += monto_base
            else:
                grupo["total_egresos"] += monto_base

        resumen_por_metodo_pago = list(grupos.values())

        return {
            "id_caja_sesion": id_caja_sesion,
            "monto_esperado_total": monto_esperado_total,
            "resumen_por_metodo_pago": resumen_por_metodo_pago,
        }

    @staticmethod
    def cerrar_caja_sesion_con_detalles(
        db: Session,
        current_user: Usuario,
        id_caja_sesion: int,
        cierres: list[dict],
    ):
        CajaService._validar_usuario_activo(current_user)

        if not cierres:
            raise ValueError("Debe enviar al menos un cierre de caja.")

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

        if caja_sesion.estado == "Cerrado":
            raise ValueError("La sesion de caja ya esta cerrada.")

        cierres_creados: list[CajaCierreDetalle] = []
        total_monto_real = Decimal("0.00")
        total_monto_esperado = Decimal("0.00")
        movimiento_cierre: MovimientoCaja | None = None

        try:
            for cierre in cierres:
                metodo_pago = db.query(MetodoPago).filter(
                    MetodoPago.id_metodo_pago == cierre["id_metodo_pago"]
                ).first()
                if metodo_pago is None:
                    raise LookupError("Metodo de pago no encontrado.")

                detalle = CajaCierreDetalle(
                    id_caja_sesion=id_caja_sesion,
                    id_metodo_pago=cierre["id_metodo_pago"],
                    monto_esperado=cierre["monto_esperado"],
                    monto_real=cierre["monto_real"],
                    diferencia=cierre["diferencia"],
                    observacion=cierre.get("observacion"),
                )
                db.add(detalle)
                db.flush()
                db.refresh(detalle)
                cierres_creados.append(detalle)
                total_monto_real += Decimal(detalle.monto_real or 0)
                total_monto_esperado += Decimal(detalle.monto_esperado or 0)

            # El monto_final será exactamente la suma de los 'monto_esperado'
            caja_sesion.monto_final = total_monto_esperado
            caja_sesion.estado = "Cerrado"
            caja_sesion.fecha_cierre = datetime.now()

            tipo_cierre = db.query(TipoMovimientoCaja).filter(
                TipoMovimientoCaja.nombre == "CIERRE"
            ).first()
            if tipo_cierre is None:
                raise LookupError("Tipo de movimiento CIERRE no encontrado.")

            movimiento_cierre = MovimientoCajaRepository.crear_movimiento(
                db=db,
                datos={
                    "id_metodo_pago": None,
                    "id_tipo_movimiento_caja": tipo_cierre.id_tipo_movimiento_caja,
                    "id_caja_sesion": caja_sesion.id_caja_sesion,
                    "id_usuario": current_user.id_usuario,
                    "fecha": datetime.now(),
                    "monto": caja_sesion.monto_final,
                    "concepto": f"CIERRE {caja_sesion.id_caja_sesion}",
                },
            )

            db.commit()
            db.refresh(caja_sesion)
            db.refresh(movimiento_cierre)
            for detalle in cierres_creados:
                db.refresh(detalle)

            return {
                "id_caja_sesion": caja_sesion.id_caja_sesion,
                "monto_inicial": caja_sesion.monto_inicial,
                "monto_total_real": total_monto_real,
                "monto_total_esperado": total_monto_esperado,
                "monto_final": caja_sesion.monto_final,
                "estado": caja_sesion.estado,
                "fecha_cierre": caja_sesion.fecha_cierre,
                "movimiento_cierre": movimiento_cierre,
                "cierres": cierres_creados,
            }
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo cerrar la sesion de caja.") from exc
        except Exception:
            db.rollback()
            raise
