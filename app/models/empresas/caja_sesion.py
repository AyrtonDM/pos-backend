from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class CajaSesion(Base):
    __tablename__ = "caja_sesion"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('Abierto', 'Cerrado')",
            name="ck_caja_sesion_estado",
        ),
    )

    id_caja_sesion = Column(Integer, primary_key=True, index=True)
    id_caja = Column(ForeignKey("caja.id_caja"), nullable=False)
    fecha_apertura = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_cierre = Column(DateTime, nullable=True)
    monto_inicial = Column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    monto_final = Column(Numeric(12, 2), nullable=True)
    estado = Column(String(20), default="Abierto", nullable=False)
    nota = Column(Text, nullable=True)

    caja = relationship("Caja", back_populates="sesiones")
