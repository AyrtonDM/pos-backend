from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class PlantillaReporte(BaseModel):
    identificador: str
    nombre: str
    descripcion: str
    metricas: list[str] = Field(default_factory=list)
    dimensiones: list[str] = Field(default_factory=list)
    formato: str = "tabla"
    filtros_por_defecto: dict[str, Any] = Field(default_factory=dict)
    etiquetas: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SolicitudReporte(BaseModel):
    prompt: str


class EspecificacionReporte(BaseModel):
    identificador_plantilla: str
    titulo: str
    metricas: list[str] = Field(default_factory=list)
    dimensiones: list[str] = Field(default_factory=list)
    filtros: dict[str, Any] = Field(default_factory=dict)
    formato: str = "tabla"
    solicita_aclaracion: bool = False
    pregunta: str | None = None
    confianza: float | None = None

    class Config:
        from_attributes = True


class ColumnaReporte(BaseModel):
    nombre: str
    etiqueta: str
    tipo: str = "texto"


class RespuestaReporte(BaseModel):
    id_reporte: str
    titulo: str
    identificador_plantilla: str
    estado: str = "listo"
    especificacion: EspecificacionReporte | None = None
    columnas: list[ColumnaReporte] = Field(default_factory=list)
    filas: list[dict[str, Any]] = Field(default_factory=list)
    agregados: dict[str, Any] = Field(default_factory=dict)
    grafico: dict[str, Any] | None = None
    advertencias: list[str] = Field(default_factory=list)
    fecha_generacion: date | None = None


class RespuestaInterpretacion(BaseModel):
    especificacion: EspecificacionReporte
    plantilla: PlantillaReporte | None = None
    advertencias: list[str] = Field(default_factory=list)