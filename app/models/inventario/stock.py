from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stock"

    id_stock = Column(Integer, primary_key=True, index=True)
    id_producto = Column(ForeignKey("producto.id_producto"), nullable=False)
    id_sucursal = Column(ForeignKey("sucursal.id_sucursal"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=0)
    stock_minimo = Column(Integer, nullable=True, default=0)
    stock_maximo = Column(Integer, nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    producto = relationship("Producto", back_populates="stocks")
    sucursal = relationship("Sucursal", back_populates="stocks")
