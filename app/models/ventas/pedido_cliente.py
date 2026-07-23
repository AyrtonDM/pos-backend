from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PedidoCliente(Base):
    __tablename__ = "pedido_cliente"

    id_pedido = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=False, index=True)
    id_sucursal = Column(ForeignKey("sucursal.id_sucursal"), nullable=False, index=True)
    id_cliente = Column(ForeignKey("cliente.id_cliente"), nullable=False, index=True)
    id_venta = Column(ForeignKey("venta.id_venta"), nullable=True, index=True)

    estado = Column(String(50), nullable=False, default="enviado")
    subtotal_estimado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    descuento_estimado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_estimado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    observacion_cliente = Column(Text, nullable=True)
    observacion_empresa = Column(Text, nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_confirmacion = Column(DateTime, nullable=True)
    fecha_preparacion = Column(DateTime, nullable=True)
    fecha_listo = Column(DateTime, nullable=True)
    fecha_cancelacion = Column(DateTime, nullable=True)

    empresa = relationship("Empresa", backref="pedidos_cliente")
    sucursal = relationship("Sucursal", backref="pedidos_cliente")
    cliente = relationship("Cliente", backref="pedidos_cliente")
    venta = relationship("Venta", back_populates="pedido", foreign_keys="[Venta.id_pedido]", uselist=False)
    detalles = relationship(
        "PedidoClienteDetalle",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )

