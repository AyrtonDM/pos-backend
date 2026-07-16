# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.models.empresas.configuracion_sistema import ConfiguracionSistema

class ConfiguracionSistemaRepository:
    @staticmethod
    def obtener_por_empresa(db: Session, id_empresa: int) -> ConfiguracionSistema | None:
        return db.query(ConfiguracionSistema).filter(ConfiguracionSistema.id_empresa == id_empresa).first()

    @staticmethod
    def crear_valores_defecto(db: Session, id_empresa: int) -> ConfiguracionSistema:
        config = ConfiguracionSistema(
            id_empresa=id_empresa,
            tema="claro",
            idioma="es",
            zona_horaria="America/La_Paz",
            moneda="BOB",
            activar_notificaciones_push=True,
            activar_sonido=True,
            activar_vibracion=True,
            confirmar_antes_de_eliminar=True,
            cerrar_sesion_por_inactividad=False,
            minutos_inactividad=15,
            imprimir_automaticamente=False,
            numero_copias=1,
            tamano_ticket="80mm"
        )
        db.add(config)
        db.flush()
        return config

    @staticmethod
    def actualizar(db: Session, config: ConfiguracionSistema, datos: dict) -> ConfiguracionSistema:
        for key, value in datos.items():
            setattr(config, key, value)
        db.flush()
        return config
