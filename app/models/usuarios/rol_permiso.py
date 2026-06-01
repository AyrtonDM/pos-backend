from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    __table_args__ = (
        UniqueConstraint("id_rol", "id_permiso", name="uq_rol_permiso"),
    )

    id_rol_permiso = Column(Integer, primary_key=True, index=True)
    id_rol = Column(ForeignKey("rol.id_rol"), nullable=False, index=True)
    id_permiso = Column(ForeignKey("permiso.id_permiso"), nullable=False, index=True)
    activo = Column(Boolean, default=True, nullable=False)

    rol = relationship("Rol", back_populates="roles_permisos")
    permiso = relationship("Permiso", back_populates="roles_permisos")
