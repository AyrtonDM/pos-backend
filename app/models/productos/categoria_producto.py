from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoriaProducto(Base):
    __tablename__ = "categoria_producto"

    id_categoria_producto = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=True)
    nombre = Column(String(150), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    empresa = relationship("Empresa", back_populates="categorias_producto")
    subcategorias = relationship(
        "SubcategoriaProducto",
        back_populates="categoria_producto",
        cascade="all, delete-orphan",
    )
