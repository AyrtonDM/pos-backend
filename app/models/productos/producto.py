from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Producto(Base):
    __tablename__ = "producto"

    id_producto = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=False)
    id_subcategoria = Column(ForeignKey("subcategoria_producto.id_subcategoria"), nullable=False)
    nombre = Column(String(150), nullable=False)
    costo = Column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    precio = Column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    imagen = Column(String(255), nullable=True)

    empresa = relationship("Empresa", back_populates="productos")
    subcategoria = relationship("SubcategoriaProducto", back_populates="productos")
    stock = relationship(
        "Stock",
        back_populates="producto",
        uselist=False,
        cascade="all, delete-orphan",
    )