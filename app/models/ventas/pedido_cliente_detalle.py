from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class PedidoClienteDetalle(Base):
    __tablename__ = "pedido_cliente_detalle"

    id_detalle = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(ForeignKey("pedido_cliente.id_pedido"), nullable=False, index=True)
    id_producto = Column(ForeignKey("producto.id_producto"), nullable=False, index=True)

    cantidad = Column(Integer, nullable=False)
    precio_unitario_estimado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    descuento_estimado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    subtotal_estimado = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    pedido = relationship("PedidoCliente", back_populates="detalles")
    producto = relationship("Producto", backref="detalles_pedido_cliente")
