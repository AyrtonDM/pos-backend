# -*- coding: utf-8 -*-
from decimal import Decimal

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoriaCliente(Base):
    __tablename__ = "categoria_cliente"

    id_categoria_cliente = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa"), nullable=False, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    permite_credito = Column(Boolean, default=True, nullable=False)
    descuento_base = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    limite_credito = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    empresa = relationship("Empresa", back_populates="categorias_cliente")
    clientes = relationship(
        "Cliente",
        back_populates="categoria_cliente",
        cascade="all, delete-orphan",
    )
