from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TipoMovimientoCaja(Base):
    __tablename__ = "tipo_movimiento_caja"

    id_tipo_movimiento_caja = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)

    movimientos = relationship("MovimientoCaja", back_populates="tipo_movimiento_caja")