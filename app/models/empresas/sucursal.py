from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Sucursal(Base):
    __tablename__ = "sucursal"

    id_sucursal = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=False)
    nombre = Column(String(150), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(30), nullable=False)
    ciudad = Column(String(100), nullable=False)
    fecha_registro = Column(Date, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    empresa = relationship("Empresa", back_populates="sucursales")
    usuario_roles = relationship("UsuarioRol", back_populates="sucursal")
    cajas = relationship("Caja", back_populates="sucursal", cascade="all, delete-orphan")
    stocks = relationship("Stock", back_populates="sucursal", cascade="all, delete-orphan")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="sucursal")
