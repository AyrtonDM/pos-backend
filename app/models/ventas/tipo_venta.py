from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TipoVenta(Base):
    __tablename__ = "tipo_venta"

    id_tipo_venta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)

    ventas = relationship("Venta", back_populates="tipo_venta")
