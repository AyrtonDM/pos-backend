from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Rol(Base):
    __tablename__ = "rol"

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    usuario_roles = relationship("UsuarioRol", back_populates="rol")
