from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class DispositivoToken(Base):
    __tablename__ = "dispositivos_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    uid_usuario = Column(String, nullable=True)
    rol = Column(String, nullable=True)
    plataforma = Column(String, nullable=True)
    id_empresa = Column(Integer, nullable=True, index=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)


class NotificacionHistorial(Base):
    __tablename__ = "notificaciones_historial"

    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, nullable=True, index=True)
    prioridad = Column(Integer, nullable=False, default=0)
    tipo = Column(String, nullable=False)
    titulo = Column(String, nullable=False)
    mensaje = Column(String, nullable=False)
    payload = Column(JSONB, nullable=True)
    leido = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)
