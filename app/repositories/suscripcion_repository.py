# -*- coding: utf-8 -*-
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.empresas.historial_suscripcion import HistorialSuscripcion
from app.models.empresas.plan import Plan
from app.models.empresas.plan_modulo import PlanModulo


class SuscripcionRepository:
    """
    Repositorio de HistorialSuscripcion enfocado en el flujo de pago Stripe.
    Sigue el patron de metodos estaticos con Session del resto del proyecto.
    """

    @staticmethod
    def obtener_por_stripe_session(
        db: Session,
        stripe_session_id: str,
    ) -> HistorialSuscripcion | None:
        """Clave de idempotencia: busca un historial ya procesado por session_id."""
        return (
            db.query(HistorialSuscripcion)
            .filter(HistorialSuscripcion.stripe_session_id == stripe_session_id)
            .first()
        )

    @staticmethod
    def obtener_por_stripe_payment_intent(
        db: Session,
        stripe_payment_intent_id: str,
    ) -> HistorialSuscripcion | None:
        """Busca un historial por PaymentIntent (util para eventos de reembolso)."""
        return (
            db.query(HistorialSuscripcion)
            .filter(
                HistorialSuscripcion.stripe_payment_intent_id == stripe_payment_intent_id
            )
            .first()
        )

    @staticmethod
    def obtener_suscripcion_activa(
        db: Session,
        id_empresa: int,
    ) -> HistorialSuscripcion | None:
        """Retorna la suscripcion activa vigente de la empresa, si existe."""
        hoy = date.today()
        return (
            db.query(HistorialSuscripcion)
            .options(
                joinedload(HistorialSuscripcion.plan)
                .joinedload(Plan.planes_modulo)
                .joinedload(PlanModulo.modulo)
            )
            .filter(
                HistorialSuscripcion.id_empresa == id_empresa,
                HistorialSuscripcion.estado == "activo",
                HistorialSuscripcion.fecha_fin >= hoy,
            )
            .order_by(HistorialSuscripcion.fecha_fin.desc())
            .first()
        )

    @staticmethod
    def crear_suscripcion(
        db: Session,
        datos: dict,
    ) -> HistorialSuscripcion:
        """Crea un nuevo registro en historial_suscripcion y hace flush."""
        suscripcion = HistorialSuscripcion(**datos)
        db.add(suscripcion)
        db.flush()
        db.refresh(suscripcion)
        return suscripcion

    @staticmethod
    def actualizar_suscripcion(
        db: Session,
        suscripcion: HistorialSuscripcion,
        datos: dict,
    ) -> HistorialSuscripcion:
        """Actualiza campos de un historial existente y hace flush."""
        for campo, valor in datos.items():
            setattr(suscripcion, campo, valor)
        db.flush()
        db.refresh(suscripcion)
        return suscripcion
