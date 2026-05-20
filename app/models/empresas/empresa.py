from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id_empresa = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    razon_social = Column(String(200), nullable=False)
    nit = Column(String(30), nullable=False, unique=True, index=True)
    correo = Column(String(255), nullable=False, unique=True, index=True)
    fecha_creacion = Column(Date, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    categorias_cliente = relationship("CategoriaCliente", back_populates="empresa", cascade="all, delete-orphan")
    clientes = relationship("Cliente", back_populates="empresa", cascade="all, delete-orphan")
    categorias_producto = relationship("CategoriaProducto", back_populates="empresa")
    productos = relationship("Producto", back_populates="empresa")
    sucursales = relationship("Sucursal", back_populates="empresa", cascade="all, delete-orphan")
    usuario_roles = relationship("UsuarioRol", back_populates="empresa")
