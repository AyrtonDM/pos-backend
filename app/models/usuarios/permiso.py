from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Permiso(Base):
    __tablename__ = "permiso"

    id_permiso = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), nullable=False, unique=True, index=True)
    nombre = Column(String(150), nullable=False)
    id_modulo = Column(ForeignKey("modulo.id_modulo"), nullable=False, index=True)

    modulo = relationship("Modulo", back_populates="permisos")
    roles_permisos = relationship("RolPermiso", back_populates="permiso", cascade="all, delete-orphan")
