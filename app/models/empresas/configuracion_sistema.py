# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"

    id_configuracion = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Apariencia
    tema = Column(String(50), default="claro", nullable=False)
    idioma = Column(String(10), default="es", nullable=False)
    zona_horaria = Column(String(100), default="America/La_Paz", nullable=False)
    moneda = Column(String(20), default="BOB", nullable=False)
    
    # Notificaciones
    activar_notificaciones_push = Column(Boolean, default=True, nullable=False)
    activar_sonido = Column(Boolean, default=True, nullable=False)
    activar_vibracion = Column(Boolean, default=True, nullable=False)
    
    # Seguridad
    confirmar_antes_de_eliminar = Column(Boolean, default=True, nullable=False)
    cerrar_sesion_por_inactividad = Column(Boolean, default=False, nullable=False)
    minutos_inactividad = Column(Integer, default=15, nullable=False)
    
    # Impresion
    imprimir_automaticamente = Column(Boolean, default=False, nullable=False)
    numero_copias = Column(Integer, default=1, nullable=False)
    tamano_ticket = Column(String(50), default="80mm", nullable=False)

    empresa = relationship("Empresa", backref="configuracion")
