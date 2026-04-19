from datetime import date

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class UsuarioRol(Base):
    __tablename__ = "usuario_rol"
    __table_args__ = (UniqueConstraint("id_usuario", "id_rol", name="uq_usuario_rol"),)

    id_usuario_rol = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_rol = Column(ForeignKey("rol.id_rol"), nullable=False)
    fecha = Column(Date, default=date.today, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    usuario = relationship("Usuario", back_populates="usuario_roles")
    rol = relationship("Rol", back_populates="usuario_roles")
