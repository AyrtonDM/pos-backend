# -*- coding: utf-8 -*-
from pydantic import BaseModel

class ConfiguracionSistemaBase(BaseModel):
    tema: str
    idioma: str
    zona_horaria: str
    moneda: str
    activar_notificaciones_push: bool
    activar_sonido: bool
    activar_vibracion: bool
    confirmar_antes_de_eliminar: bool
    cerrar_sesion_por_inactividad: bool
    minutos_inactividad: int
    imprimir_automaticamente: bool
    numero_copias: int
    tamano_ticket: str

class ConfiguracionSistemaUpdate(ConfiguracionSistemaBase):
    pass

class ConfiguracionSistemaResponse(ConfiguracionSistemaBase):
    id_configuracion: int
    id_empresa: int

    class Config:
        from_attributes = True
