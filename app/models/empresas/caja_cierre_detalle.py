from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CajaCierreDetalle(Base):
    __tablename__ = "caja_cierre_detalle"

    id_caja_cierre_detalle = Column(Integer, primary_key=True, index=True)
    id_metodo_pago = Column(ForeignKey("metodo_pago.id_metodo_pago"), nullable=False, index=True)
    id_caja_sesion = Column(ForeignKey("caja_sesion.id_caja_sesion"), nullable=False, index=True)
    monto_esperado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    monto_real = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    diferencia = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    observacion = Column(Text, nullable=True)

    metodo_pago = relationship("MetodoPago", back_populates="cierres_caja")
    caja_sesion = relationship("CajaSesion", back_populates="cierres_detalle")