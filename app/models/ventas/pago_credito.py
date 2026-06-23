from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class PagoCredito(Base):
    __tablename__ = "pago_credito"

    id_pago_credito = Column(Integer, primary_key=True, index=True)
    id_cxc = Column(ForeignKey("cuenta_por_cobrar.id_cxc"), nullable=False, index=True)
    id_metodo_pago = Column(ForeignKey("metodo_pago.id_metodo_pago"), nullable=False, index=True)
    monto_pagado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    fecha_pago = Column(DateTime, default=datetime.utcnow, nullable=False)

    cuenta_por_cobrar = relationship("CuentaPorCobrar", back_populates="pagos_credito")
    metodo_pago = relationship("MetodoPago", back_populates="pagos_credito")
