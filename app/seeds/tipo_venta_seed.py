from sqlalchemy.orm import Session

from app.models.ventas.tipo_venta import TipoVenta

DEFAULT_TIPOS_VENTA = [
    {
        "id_tipo_venta": 1,
        "nombre": "Contado",
        "descripcion": "Venta al contado",
    },
    {
        "id_tipo_venta": 2,
        "nombre": "Credito",
        "descripcion": "Venta al Credito",
    },
]


def seed_tipos_venta(db: Session) -> None:
    for tipo_data in DEFAULT_TIPOS_VENTA:
        existe = (
            db.query(TipoVenta)
            .filter(TipoVenta.id_tipo_venta == tipo_data["id_tipo_venta"])
            .first()
        )
        if not existe:
            db.add(TipoVenta(**tipo_data))