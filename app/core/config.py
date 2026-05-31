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


def resolver_ruta(base: Path, valor: str | None) -> Path | None:
	if not valor:
		return None

	ruta = Path(valor)
	if ruta.is_absolute():
		return ruta

	return (base / ruta).resolve()
