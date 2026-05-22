from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class MetodoPago(Base):
    __tablename__ = "metodo_pago"

    id_metodo_pago = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)

    ventas_pago = relationship("VentaPago", back_populates="metodo_pago")
    movimientos_caja = relationship("MovimientoCaja", back_populates="metodo_pago")
    cierres_caja = relationship("CajaCierreDetalle", back_populates="metodo_pago")