from decimal import Decimal
from sqlalchemy import Column, Integer, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DetalleVenta(Base):
    __tablename__ = "detalle_venta"

    id_detalle_venta = Column(Integer, primary_key=True, index=True)
    id_venta = Column(ForeignKey("venta.id_venta"), nullable=False)
    id_producto = Column(ForeignKey("producto.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    descuento = Column(Numeric(12, 2), default=0)
    subtotal = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    descripcion = Column(Text, nullable=True)

    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto")
