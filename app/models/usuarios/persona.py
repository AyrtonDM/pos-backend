from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Persona(Base):
    __tablename__ = "persona"

    id_persona = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(150), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String(20), nullable=False)
    telefono = Column(String(20), nullable=False)
    documento = Column(String(30), nullable=False, unique=True)

    usuario = relationship("Usuario", back_populates="persona", uselist=False)
