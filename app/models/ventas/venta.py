from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Venta(Base):
    __tablename__ = "venta"

    id_venta = Column(Integer, primary_key=True, index=True)
    id_tipo_venta = Column(ForeignKey("tipo_venta.id_tipo_venta"), nullable=False, index=True)
    id_cliente = Column(ForeignKey("cliente.id_cliente"), nullable=True, index=True)
    id_caja_sesion = Column(ForeignKey("caja_sesion.id_caja_sesion"), nullable=False, index=True)
    id_usuario = Column(ForeignKey("usuario.id_usuario"), nullable=False, index=True)

    subtotal = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    descuento_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    estado = Column(String(50), nullable=False)

    tipo_venta = relationship("TipoVenta", back_populates="ventas")
    cliente = relationship("Cliente", back_populates="ventas")
    caja_sesion = relationship("CajaSesion", back_populates="ventas")
    usuario = relationship("Usuario", back_populates="ventas")
    pagos = relationship("VentaPago", back_populates="venta", cascade="all, delete-orphan")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")