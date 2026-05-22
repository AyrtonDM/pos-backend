from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class MovimientoCaja(Base):
    __tablename__ = "movimiento_caja"

    id_movimiento_caja = Column(Integer, primary_key=True, index=True)
    id_metodo_pago = Column(ForeignKey("metodo_pago.id_metodo_pago"), nullable=False, index=True)
    id_tipo_movimiento_caja = Column(
        ForeignKey("tipo_movimiento_caja.id_tipo_movimiento_caja"),
        nullable=False,
        index=True,
    )
    id_caja_sesion = Column(ForeignKey("caja_sesion.id_caja_sesion"), nullable=False, index=True)
    id_usuario = Column(ForeignKey("usuario.id_usuario"), nullable=False, index=True)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)

    metodo_pago = relationship("MetodoPago", back_populates="movimientos_caja")
    tipo_movimiento_caja = relationship("TipoMovimientoCaja", back_populates="movimientos")
    caja_sesion = relationship("CajaSesion", back_populates="movimientos_caja")
    usuario = relationship("Usuario", back_populates="movimientos_caja")