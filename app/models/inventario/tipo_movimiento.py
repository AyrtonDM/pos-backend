from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TipoMovimiento(Base):
    __tablename__ = "tipo_movimiento"

    id_tipo_movimiento = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)
    direccion = Column(String(20), nullable=False)

    movimientos = relationship("MovimientoInventario", back_populates="tipo_movimiento")
