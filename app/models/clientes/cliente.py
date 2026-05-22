# -*- coding: utf-8 -*-
from decimal import Decimal

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(ForeignKey("usuario.id_usuario"), nullable=False, index=True)
    id_categoria_cliente = Column(
        ForeignKey("categoria_cliente.id_categoria_cliente"), nullable=True, index=True
    )
    codigo_cliente = Column(String(50), nullable=False, index=True)
    saldo_credito = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=True)
    limite_credito = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("id_usuario", "codigo_cliente", name="uq_cliente_usuario_codigo"),
    )

    usuario = relationship("Usuario", back_populates="clientes")
    categoria_cliente = relationship("CategoriaCliente", back_populates="clientes")
    ventas = relationship("Venta", back_populates="cliente")
