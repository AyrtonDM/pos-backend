# -*- coding: utf-8 -*-
"""
Router de pagos con Stripe Checkout.

Endpoints:
  POST /api/pagos/checkout   — Crear sesion de pago (requiere JWT)
  POST /api/pagos/confirmar  — Confirmar pago desde frontend (requiere JWT)
  POST /api/pagos/webhook    — Handler de eventos Stripe (sin JWT, firma Stripe)
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios.usuario import Usuario
from app.schemas.pago_schema import (
    CheckoutRequest,
    CheckoutResponse,
    ConfirmarPagoRequest,
    ConfirmarPagoResponse,
)
from app.services.pago_service import PagoService
from app.services.bitacora_service import registrar_accion

router = APIRouter(prefix="/api/pagos", tags=["pagos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------ #
# POST /api/pagos/checkout                                            #
# ------------------------------------------------------------------ #

@router.post("/checkout", response_model=CheckoutResponse)
def crear_checkout(
    datos: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Crea una sesión de Stripe Checkout para el plan indicado.
    El frontend debe redirigir al usuario a checkout_url.
    """
    try:
        resultado = PagoService.crear_checkout_session(
            db=db,
            current_user=current_user,
            id_empresa=datos.id_empresa,
            id_plan=datos.id_plan,
        )
        try:
            registrar_accion(
                usuario_nombre=current_user.email,
                accion=f"Registró pago ID: {resultado.session_id}, monto: {resultado.monto}",
                empresa_nombre=str(datos.id_empresa)
            )
        except Exception:
            pass
        return resultado
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=500, detail="Error al crear la sesión de pago."
        )


# ------------------------------------------------------------------ #
# POST /api/pagos/confirmar                                           #
# ------------------------------------------------------------------ #

@router.post("/confirmar", response_model=ConfirmarPagoResponse)
def confirmar_pago(
    datos: ConfirmarPagoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Confirma el pago verificando el estado real contra Stripe.
    Activa o renueva la suscripción en HistorialSuscripcion.
    Idempotente: llamadas repetidas con el mismo session_id retornan el mismo resultado.
    """
    try:
        resultado = PagoService.confirmar_pago(
            db=db,
            current_user=current_user,
            session_id=datos.session_id,
        )
        try:
            empresa_id = str(resultado.suscripcion.id_empresa) if resultado and hasattr(resultado, 'suscripcion') else None
            registrar_accion(
                usuario_nombre=current_user.email,
                accion=f"Confirmó pago ID: {datos.session_id}",
                empresa_nombre=empresa_id
            )
        except Exception:
            pass
        return resultado
    except PermissionError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=500, detail="Error al confirmar el pago."
        )


# ------------------------------------------------------------------ #
# POST /api/pagos/webhook                                             #
# ------------------------------------------------------------------ #

@router.post("/webhook", include_in_schema=False)
async def webhook_stripe(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Endpoint público — sin JWT. Se autentica exclusivamente por la firma
    Stripe-Signature usando STRIPE_WEBHOOK_SECRET.

    CRÍTICO: el body se lee como bytes crudos ANTES de cualquier parseo
    de FastAPI para que la verificación de firma de Stripe funcione.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=400,
            detail="Falta el header Stripe-Signature.",
        )

    # Leer body como bytes crudos (obligatorio para stripe.Webhook.construct_event)
    payload: bytes = await request.body()

    try:
        return PagoService.procesar_webhook(
            db=db,
            payload=payload,
            stripe_signature=stripe_signature,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error procesando el webhook: {str(e)}"
        )
