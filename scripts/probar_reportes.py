from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.reporte_schema import SolicitudReporte
from app.services.reportes_service import ReportesService


def main() -> None:
    solicitud = SolicitudReporte(prompt="Quiero un resumen de ventas del ultimo mes por sucursal")
    especificacion, advertencias = ReportesService.interpretar_solicitud(solicitud)
    if hasattr(especificacion, "model_dump"):
        especificacion_dict = especificacion.model_dump()
        plantillas = [plantilla.model_dump() for plantilla in ReportesService.obtener_catalogo()]
    else:
        especificacion_dict = especificacion.dict()
        plantillas = [plantilla.dict() for plantilla in ReportesService.obtener_catalogo()]
    salida = {
        "advertencias": advertencias,
        "especificacion": especificacion_dict,
        "plantillas": plantillas,
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()