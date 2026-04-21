from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"

    id_movimiento_inventario = Column(Integer, primary_key=True, index=True)
    id_producto = Column(ForeignKey("producto.id_producto"), nullable=False)
    id_tipo_movimiento = Column(ForeignKey("tipo_movimiento.id_tipo_movimiento"), nullable=False)
    id_usuario = Column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_sucursal = Column(ForeignKey("sucursal.id_sucursal"), nullable=True)
    cantidad = Column(Integer, nullable=False)
    observacion = Column(Text, nullable=True)
    fecha_movimiento = Column(DateTime, default=datetime.utcnow, nullable=False)

    producto = relationship("Producto", back_populates="movimientos_inventario")
    tipo_movimiento = relationship("TipoMovimiento", back_populates="movimientos")
    usuario = relationship("Usuario", back_populates="movimientos_inventario")
    sucursal = relationship("Sucursal", back_populates="movimientos_inventario")
