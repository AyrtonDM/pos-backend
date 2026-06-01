from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class HistorialSuscripcion(Base):
    __tablename__ = "historial_suscripcion"

    id_historial_suscripcion   = Column(Integer, primary_key=True, index=True)
    id_plan                    = Column(ForeignKey("plan.id_plan"), nullable=False, index=True)
    id_empresa                 = Column(ForeignKey("empresa.id_empresa"), nullable=False, index=True)
    fecha_inicio               = Column(Date, nullable=False)
    fecha_fin                  = Column(Date, nullable=True)
    estado                     = Column(String(50), nullable=False)
    # --- Stripe Checkout (idempotencia y trazabilidad, sin tabla nueva) ---
    stripe_session_id          = Column(String(255), unique=True, nullable=True, index=True)
    stripe_payment_intent_id   = Column(String(255), nullable=True)
    stripe_payment_status      = Column(String(50), nullable=True)

    plan    = relationship("Plan", back_populates="historial_suscripciones")
    empresa = relationship("Empresa", back_populates="historial_suscripciones")

