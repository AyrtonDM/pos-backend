from datetime import date

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Caja(Base):
    __tablename__ = "caja"

    id_caja = Column(Integer, primary_key=True, index=True)
    id_sucursal = Column(ForeignKey("sucursal.id_sucursal"), nullable=False)
    nombre = Column(String(150), nullable=False)
    codigo = Column(String(50), nullable=False)
    fecha_creacion = Column(Date, default=date.today, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    sucursal = relationship("Sucursal", back_populates="cajas")
