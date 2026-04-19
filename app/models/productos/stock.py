from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stock"

    id_stock = Column(Integer, primary_key=True, index=True)
    id_producto = Column(ForeignKey("producto.id_producto", ondelete="CASCADE"), nullable=False, unique=True)
    cantidad = Column(Integer, default=0, nullable=False)
    stock_min = Column(Integer, default=0, nullable=False)
    stock_max = Column(Integer, default=0, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    producto = relationship("Producto", back_populates="stock")