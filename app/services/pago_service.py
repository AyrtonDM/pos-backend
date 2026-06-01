# -*- coding: utf-8 -*-
"""
PagoService — Integración con Stripe Checkout (pago único por ciclo).

Decisiones de diseño:
- Sin Stripe Subscriptions.
- La suscripción se rige por HistorialSuscripcion en nuestra BD.
- stripe_session_id es la clave de idempotencia (UNIQUE en BD).
- _activar_suscripcion() es reutilizada por confirmar_pago() y procesar_webhook(),
  garantizando que ambos caminos sean equivalentes e idempotentes.
- IntegrityError capturado para manejar concurrencia (webhook + frontend simultáneos).
"""
from datetime import date, timedelta
from decimal import Decimal

import stripe
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import (
    obtener_stripe_cancel_url,
    obtener_stripe_secret_key,
    obtener_stripe_success_url,
    obtener_stripe_webhook_secret,
)
from app.models.empresas.historial_suscripcion import HistorialSuscripcion
from app.models.empresas.plan import Plan
from app.models.usuarios.usuario import Usuario
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.suscripcion_repository import SuscripcionRepository

# Duración del ciclo de suscripción en días.
# Si en el futuro se agrega Plan.duracion_dias, leer de ahí en su lugar.
DURACION_PLAN_DIAS: int = 30


class PagoService:

    @staticmethod
    def _init_stripe() -> None:
        """Inicializa la clave de API de Stripe antes de cada llamada."""
        stripe.api_key = obtener_stripe_secret_key()

    # ------------------------------------------------------------------ #
    # Crear sesión de Checkout                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def crear_checkout_session(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_plan: int,
    ) -> dict:
        """
        Crea una Stripe Checkout Session para que el usuario realice el pago.

        Returns:
            dict con checkout_url, session_id, plan_nombre, monto, moneda.

        Raises:
            PermissionError: si el usuario no es administrador de la empresa.
            LookupError: si el plan no existe.
            ValueError: si el plan no tiene precio configurado.
        """
        # 1. Verificar que el usuario tiene acceso a la empresa
        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise PermissionError(
                "No tienes permisos de administrador para esta empresa."
            )

        # 2. Obtener y validar plan
        plan: Plan | None = db.query(Plan).filter(Plan.id_plan == id_plan).first()
        if plan is None:
            raise LookupError("Plan no encontrado.")
        if plan.precio <= Decimal("0.00"):
            raise ValueError("El plan no tiene precio configurado.")

        # 3. Convertir a centavos (Stripe requiere entero, no decimales)
        monto_centavos = int(plan.precio * 100)

        # 4. Crear sesión en Stripe
        PagoService._init_stripe()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": plan.nombre,
                            "description": plan.descripcion,
                        },
                        "unit_amount": monto_centavos,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            # {CHECKOUT_SESSION_ID} es un placeholder de Stripe, no Python
            success_url=(
                obtener_stripe_success_url() + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=obtener_stripe_cancel_url(),
            metadata={
                "id_empresa": str(id_empresa),
                "id_plan": str(id_plan),
                "id_usuario": str(current_user.id_usuario),
            },
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "plan_nombre": plan.nombre,
            "monto": str(plan.precio),
            "moneda": "usd",
        }

    # ------------------------------------------------------------------ #
    # Confirmar pago desde frontend (con session_id de Stripe)            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def confirmar_pago(
        db: Session,
        current_user: Usuario,
        session_id: str,
    ) -> dict:
        """
        Verifica el estado real del pago contra Stripe y activa la suscripción.
        Nunca confía solo en el frontend: siempre consulta Stripe.

        Returns:
            dict con mensaje y suscripcion activada.

        Raises:
            ValueError: si el session_id es inválido.
            PermissionError: si el pago no fue completado.
        """
        PagoService._init_stripe()

        # 1. Recuperar sesión de Stripe para verificar estado real
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.InvalidRequestError as exc:
            raise ValueError(
                "session_id inválido o no encontrado en Stripe."
            ) from exc

        # 2. Verificar que el pago fue completado
        if session.payment_status != "paid":
            raise PermissionError(
                f"El pago no fue completado. Estado actual: {session.payment_status}"
            )

        # 3. Idempotencia: si ya fue procesado, retornar el registro existente
        existente = SuscripcionRepository.obtener_por_stripe_session(
            db=db, stripe_session_id=session_id
        )
        if existente:
            return {
                "mensaje": "Este pago ya fue procesado anteriormente.",
                "suscripcion": existente,
            }

        # 4. Activar suscripción (primera vez)
        suscripcion = PagoService._activar_suscripcion(db=db, session=session)

        return {
            "mensaje": "Suscripción activada correctamente.",
            "suscripcion": suscripcion,
        }

    # ------------------------------------------------------------------ #
    # Lógica central de activación (compartida con webhook)               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _activar_suscripcion(
        db: Session,
        session: object,
    ) -> HistorialSuscripcion:
        """
        Crea el registro en HistorialSuscripcion a partir de la Session de Stripe.

        Reglas de negocio:
        - Si existe suscripción activa anterior, se cierra con estado "renovada".
        - Se crea un nuevo registro con estado "activo".
        - IntegrityError (concurrencia webhook+frontend) → retorna el registro ya creado.

        Args:
            session: objeto stripe.checkout.Session (o dict en webhook).
        """
        # Stripe puede pasar un objeto o un dict (evento webhook)
        if isinstance(session, dict):
            session_id         = session["id"]
            payment_intent_id  = session.get("payment_intent")
            payment_status     = session.get("payment_status", "paid")
            metadata           = session.get("metadata", {})
        else:
            session_id        = session.id
            payment_intent_id = session.payment_intent
            payment_status    = session.payment_status
            metadata          = session.metadata

        id_empresa = int(metadata["id_empresa"])
        id_plan    = int(metadata["id_plan"])
        hoy        = date.today()
        fecha_fin  = hoy + timedelta(days=DURACION_PLAN_DIAS)

        # Cerrar suscripción activa anterior si existe y es diferente a esta sesión
        activa = SuscripcionRepository.obtener_suscripcion_activa(
            db=db, id_empresa=id_empresa
        )
        if activa and activa.stripe_session_id != session_id:
            SuscripcionRepository.actualizar_suscripcion(
                db=db,
                suscripcion=activa,
                datos={"estado": "renovada"},
            )

        try:
            nueva = SuscripcionRepository.crear_suscripcion(
                db=db,
                datos={
                    "id_plan":                   id_plan,
                    "id_empresa":                id_empresa,
                    "fecha_inicio":              hoy,
                    "fecha_fin":                 fecha_fin,
                    "estado":                    "activo",
                    "stripe_session_id":         session_id,
                    "stripe_payment_intent_id":  payment_intent_id,
                    "stripe_payment_status":     payment_status,
                },
            )
            db.commit()
            db.refresh(nueva)
            return nueva

        except IntegrityError:
            # Condición de carrera: webhook y frontend llegaron simultáneamente.
            # El segundo hilo/proceso recibe IntegrityError por UNIQUE(stripe_session_id).
            # Hacemos rollback y devolvemos el registro ya creado.
            db.rollback()
            existente = SuscripcionRepository.obtener_por_stripe_session(
                db=db, stripe_session_id=session_id
            )
            return existente

    # ------------------------------------------------------------------ #
    # Procesar webhook de Stripe                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def procesar_webhook(
        db: Session,
        payload: bytes,
        stripe_signature: str,
    ) -> dict:
        """
        Verifica la firma del webhook y despacha el evento correspondiente.

        CRÍTICO: payload debe ser los bytes crudos del request body,
                 sin ningún parseo previo por FastAPI.

        Returns:
            {"received": True}

        Raises:
            ValueError: si la firma es inválida.
        """
        PagoService._init_stripe()

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=obtener_stripe_webhook_secret(),
            )
        except stripe.error.SignatureVerificationError as exc:
            raise ValueError("Firma de webhook inválida.") from exc

        event_type: str = event["type"]
        data_object: dict = event["data"]["object"]

        if event_type == "checkout.session.completed":
            PagoService._webhook_checkout_completado(db=db, session=data_object)

        elif event_type == "checkout.session.expired":
            # Solo logging informativo; no hay acción en BD
            pass

        elif event_type == "charge.refunded":
            PagoService._webhook_cargo_reembolsado(db=db, charge=data_object)

        # Cualquier otro evento ignorado pero respondemos 200 para evitar reintentos
        return {"received": True}

    @staticmethod
    def _webhook_checkout_completado(db: Session, session: dict) -> None:
        """
        Activa suscripción al recibir checkout.session.completed.
        Idempotente: si ya fue confirmada por el frontend, no hace nada.
        """
        session_id = session.get("id", "")
        existente = SuscripcionRepository.obtener_por_stripe_session(
            db=db, stripe_session_id=session_id
        )
        if not existente:
            PagoService._activar_suscripcion(db=db, session=session)

    @staticmethod
    def _webhook_cargo_reembolsado(db: Session, charge: dict) -> None:
        """
        Marca la suscripción como reembolsada al recibir charge.refunded.
        Solo actúa si la suscripción está activa (no reembolsa lo ya reembolsado).
        """
        payment_intent_id: str | None = charge.get("payment_intent")
        if not payment_intent_id:
            return

        suscripcion = SuscripcionRepository.obtener_por_stripe_payment_intent(
            db=db, stripe_payment_intent_id=payment_intent_id
        )
        if suscripcion and suscripcion.estado == "activo":
            SuscripcionRepository.actualizar_suscripcion(
                db=db,
                suscripcion=suscripcion,
                datos={"estado": "reembolsada"},
            )
            db.commit()
