from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    id_persona = Column(ForeignKey("persona.id_persona"), nullable=False, unique=True)
    fecha_creacion = Column(Date, default=date.today, nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    contrasena = Column(String(255), nullable=False)
    activo = Column(Boolean, default=False, nullable=False)
    codigo_verificacion_hash = Column(String(64), nullable=True)
    codigo_verificacion_expira_en = Column(DateTime, nullable=True)
    codigo_verificacion_intentos = Column(Integer, nullable=False, default=0)

    persona = relationship("Persona", back_populates="usuario")
    usuario_roles = relationship(
        "UsuarioRol", back_populates="usuario", cascade="all, delete-orphan"
    )
    movimientos_inventario = relationship("MovimientoInventario", back_populates="usuario")
    clientes = relationship("Cliente", back_populates="usuario", cascade="all, delete-orphan")
