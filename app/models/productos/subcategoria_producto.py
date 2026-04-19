from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class SubcategoriaProducto(Base):
    __tablename__ = "subcategoria_producto"

    id_subcategoria = Column(Integer, primary_key=True, index=True)
    id_categoria_producto = Column(ForeignKey("categoria_producto.id_categoria_producto"), nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    categoria_producto = relationship("CategoriaProducto", back_populates="subcategorias")
    productos = relationship("Producto", back_populates="subcategoria")