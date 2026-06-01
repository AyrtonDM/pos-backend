# -*- coding: utf-8 -*-
from datetime import date

from pydantic import BaseModel


# ------------------------------------------------------------------ #
# Crear sesion de Checkout                                            #
# ------------------------------------------------------------------ #

class CheckoutRequest(BaseModel):
    id_empresa: int
    id_plan: int


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    plan_nombre: str
    monto: str
    moneda: str


# ------------------------------------------------------------------ #
# Confirmar pago desde frontend                                       #
# ------------------------------------------------------------------ #

class ConfirmarPagoRequest(BaseModel):
    session_id: str


class SuscripcionActivadaResponse(BaseModel):
    id_historial_suscripcion: int
    id_empresa: int
    id_plan: int
    fecha_inicio: date
    fecha_fin: date | None
    estado: str
    stripe_session_id: str | None
    stripe_payment_intent_id: str | None
    stripe_payment_status: str | None

    class Config:
        from_attributes = True


class ConfirmarPagoResponse(BaseModel):
    mensaje: str
    suscripcion: SuscripcionActivadaResponse
