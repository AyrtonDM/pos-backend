from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Modulo(Base):
    __tablename__ = "modulo"

    id_modulo = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), nullable=False, unique=True, index=True)
    nombre = Column(String(150), nullable=False)

    permisos = relationship("Permiso", back_populates="modulo", cascade="all, delete-orphan")
    planes_modulo = relationship("PlanModulo", back_populates="modulo", cascade="all, delete-orphan")
