from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoriaProducto(Base):
    __tablename__ = "categoria_producto"

    id_categoria_producto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    subcategorias = relationship(
        "SubcategoriaProducto",
        back_populates="categoria_producto",
        cascade="all, delete-orphan",
    )