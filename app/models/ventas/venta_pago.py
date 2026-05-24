from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class VentaPago(Base):
    __tablename__ = "venta_pago"

    id_venta = Column(ForeignKey("venta.id_venta"), primary_key=True)
    id_metodo_pago = Column(ForeignKey("metodo_pago.id_metodo_pago"), primary_key=True)
    monto = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)

    venta = relationship("Venta", back_populates="pagos")
    metodo_pago = relationship("MetodoPago", back_populates="ventas_pago")