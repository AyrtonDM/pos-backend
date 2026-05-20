# -*- coding: utf-8 -*-
from decimal import Decimal

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=False, index=True)
    id_categoria_cliente = Column(
        ForeignKey("categoria_cliente.id_categoria_cliente"), nullable=False, index=True
    )
    codigo_cliente = Column(String(50), nullable=False, index=True)
    saldo_credito = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    limite_credito = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("id_empresa", "codigo_cliente", name="uq_cliente_empresa_codigo"),
    )

    empresa = relationship("Empresa", back_populates="clientes")
    categoria_cliente = relationship("CategoriaCliente", back_populates="clientes")
