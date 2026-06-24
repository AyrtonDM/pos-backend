from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Factura(Base):
    __tablename__ = "factura"

    id_factura = Column(Integer, primary_key=True, index=True)
    id_venta = Column(
        ForeignKey("venta.id_venta"),
        nullable=False,
        unique=True,
        index=True,
    )
    nit_emisor = Column(String(30), nullable=False)
    numero_factura = Column(Integer, nullable=False)
    fecha_emision = Column(DateTime, default=datetime.utcnow, nullable=False)
    nit_cliente = Column(String(30), nullable=False)
    monto_total = Column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    iva = Column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    cufd = Column(String(100), nullable=False)
    cuf = Column(String(200), nullable=False, unique=True, index=True)
    xml_generado = Column(Text, nullable=False)
    pdf_generado = Column(Text, nullable=False)

    venta = relationship("Venta", back_populates="factura")
