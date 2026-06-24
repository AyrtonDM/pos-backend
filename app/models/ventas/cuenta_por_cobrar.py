from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class CuentaPorCobrar(Base):
    __tablename__ = "cuenta_por_cobrar"

    id_cxc = Column(Integer, primary_key=True, index=True)
    id_venta = Column(ForeignKey("venta.id_venta"), nullable=False, index=True)
    monto_credito = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    saldo_pendiente = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    estado = Column(String(50), nullable=False)

    venta = relationship("Venta", back_populates="cuentas_por_cobrar")
    pagos_credito = relationship(
        "PagoCredito",
        back_populates="cuenta_por_cobrar",
        cascade="all, delete-orphan",
    )
