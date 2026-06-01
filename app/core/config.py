from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]


def obtener_modelo_reportes() -> str:
	return os.getenv("OPENAI_REPORT_MODEL", "gpt-5.4-mini")


def obtener_clave_openai() -> str | None:
	return os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------------------------------
# Stripe Checkout
# ---------------------------------------------------------------------------

def obtener_stripe_secret_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY no está configurada en el entorno.")
    return key


def obtener_stripe_publishable_key() -> str | None:
    return os.getenv("STRIPE_PUBLISHABLE_KEY")


def obtener_stripe_webhook_secret() -> str:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET no está configurada en el entorno.")
    return secret


def obtener_stripe_success_url() -> str:
    return os.getenv("STRIPE_SUCCESS_URL", "http://localhost:4200/pago/exitoso")


def obtener_stripe_cancel_url() -> str:
    return os.getenv("STRIPE_CANCEL_URL", "http://localhost:4200/pago/cancelado")


# ---------------------------------------------------------------------------

def resolver_ruta(base: Path, valor: str | None) -> Path | None:
	if not valor:
		return None

	ruta = Path(valor)
	if ruta.is_absolute():
		return ruta

	return (base / ruta).resolve()
