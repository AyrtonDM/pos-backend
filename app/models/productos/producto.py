from decimal import Decimal

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Producto(Base):
    __tablename__ = "producto"

    id_producto = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=True)
    id_subcategoria = Column(ForeignKey("subcategoria_producto.id_subcategoria"), nullable=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    unidad_medida = Column(String(50), nullable=False)
    precio = Column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    imagen = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    empresa = relationship("Empresa", back_populates="productos")
    subcategoria = relationship("SubcategoriaProducto", back_populates="productos")
    stocks = relationship("Stock", back_populates="producto", cascade="all, delete-orphan")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="producto")
