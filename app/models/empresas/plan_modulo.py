from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlanModulo(Base):
    __tablename__ = "plan_modulo"
    __table_args__ = (
        UniqueConstraint("id_plan", "id_modulo", name="uq_plan_modulo"),
    )

    id_plan_modulo = Column(Integer, primary_key=True, index=True)
    id_plan = Column(ForeignKey("plan.id_plan"), nullable=False, index=True)
    id_modulo = Column(ForeignKey("modulo.id_modulo"), nullable=False, index=True)
    configuracion = Column(Text, nullable=True)

    plan = relationship("Plan", back_populates="planes_modulo")
    modulo = relationship("Modulo", back_populates="planes_modulo")
