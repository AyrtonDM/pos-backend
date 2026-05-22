from sqlalchemy.orm import Session

from app.models.ventas.metodo_pago import MetodoPago

DEFAULT_METODOS_PAGO = [
    {
        "id_metodo_pago": 1,
        "nombre": "EFECTIVO",
        "descripcion": "Pago en efectivo",
    },
]


def seed_metodos_pago(db: Session) -> None:
    for metodo_data in DEFAULT_METODOS_PAGO:
        existe = (
            db.query(MetodoPago)
            .filter(MetodoPago.id_metodo_pago == metodo_data["id_metodo_pago"])
            .first()
        )
        if not existe:
            db.add(MetodoPago(**metodo_data))