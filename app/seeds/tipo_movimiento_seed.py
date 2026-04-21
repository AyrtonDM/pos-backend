from sqlalchemy.orm import Session

from app.models.inventario.tipo_movimiento import TipoMovimiento

DEFAULT_TIPOS_MOVIMIENTO = [
    {
        "id_tipo_movimiento": 1,
        "nombre": "Entrada manual",
        "descripcion": "Incrementa stock por ingreso manual",
        "direccion": "ENTRADA",
    },
    {
        "id_tipo_movimiento": 2,
        "nombre": "Salida manual",
        "descripcion": "Reduce stock por salida manual",
        "direccion": "SALIDA",
    },
    {
        "id_tipo_movimiento": 3,
        "nombre": "Venta",
        "descripcion": "Reduce stock por venta",
        "direccion": "SALIDA",
    },
    {
        "id_tipo_movimiento": 4,
        "nombre": "Ajuste positivo",
        "descripcion": "Corrige stock aumentando cantidad",
        "direccion": "ENTRADA",
    },
    {
        "id_tipo_movimiento": 5,
        "nombre": "Ajuste negativo",
        "descripcion": "Corrige stock reduciendo cantidad",
        "direccion": "SALIDA",
    },
    {
        "id_tipo_movimiento": 6,
        "nombre": "Merma",
        "descripcion": "Reduce stock por perdida o dano",
        "direccion": "SALIDA",
    },
]


def seed_tipos_movimiento(db: Session) -> None:
    for tipo_data in DEFAULT_TIPOS_MOVIMIENTO:
        existe = (
            db.query(TipoMovimiento)
            .filter(TipoMovimiento.id_tipo_movimiento == tipo_data["id_tipo_movimiento"])
            .first()
        )
        if not existe:
            db.add(TipoMovimiento(**tipo_data))
