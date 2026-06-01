from decimal import Decimal

from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plan"

    id_plan = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(255), nullable=False)
    precio = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    planes_modulo = relationship("PlanModulo", back_populates="plan", cascade="all, delete-orphan")
    historial_suscripciones = relationship(
        "HistorialSuscripcion",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
