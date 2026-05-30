from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Bitacora(Base):
    __tablename__ = "bitacora"

    id_bitacora = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(ForeignKey("usuario.id_usuario"), nullable=True, index=True)
    accion = Column(String(50), nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE
    modulo = Column(String(100), nullable=False, index=True)  # usuarios, productos, ventas, etc
    descripcion = Column(Text, nullable=True)
    ip = Column(String(45), nullable=True)  # IPv4 o IPv6
    fecha_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    usuario = relationship("Usuario", foreign_keys=[id_usuario])
