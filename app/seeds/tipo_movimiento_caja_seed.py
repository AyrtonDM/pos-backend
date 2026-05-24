from sqlalchemy.orm import Session

from app.models.empresas.tipo_movimiento_caja import TipoMovimientoCaja

DEFAULT_TIPOS_MOVIMIENTO_CAJA = [
    {
        "id_tipo_movimiento_caja": 1,
        "nombre": "APERTURA",
        "descripcion": "APERTURA",
    },
    {
        "id_tipo_movimiento_caja": 2,
        "nombre": "INGRESO",
        "descripcion": "INGRESO",
    },
    {
        "id_tipo_movimiento_caja": 3,
        "nombre": "EGRESO",
        "descripcion": "EGRESO",
    },
    {
        "id_tipo_movimiento_caja": 4,
        "nombre": "CIERRE",
        "descripcion": "CIERRE",
    },
    {
        "id_tipo_movimiento_caja": 5,
        "nombre": "AJUSTE_POSITIVO",
        "descripcion": "AJUSTE_POSITIVO",
    },
    {
        "id_tipo_movimiento_caja": 6,
        "nombre": "AJUSTE_NEGATIVO",
        "descripcion": "AJUSTE_NEGATIVO",
    },
]


def seed_tipos_movimiento_caja(db: Session) -> None:
    for tipo_data in DEFAULT_TIPOS_MOVIMIENTO_CAJA:
        existe = (
            db.query(TipoMovimientoCaja)
            .filter(
                TipoMovimientoCaja.id_tipo_movimiento_caja
                == tipo_data["id_tipo_movimiento_caja"]
            )
            .first()
        )
        if not existe:
            db.add(TipoMovimientoCaja(**tipo_data))