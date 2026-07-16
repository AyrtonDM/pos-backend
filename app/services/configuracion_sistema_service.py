# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.models.usuarios.usuario import Usuario
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.configuracion_sistema_repository import ConfiguracionSistemaRepository
from app.models.empresas.configuracion_sistema import ConfiguracionSistema

class ConfiguracionSistemaService:
    @staticmethod
    def _validar_acceso_empresa(db: Session, current_user: Usuario, id_empresa: int) -> None:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")
        
        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

    @staticmethod
    def obtener_configuracion(db: Session, current_user: Usuario, id_empresa: int) -> ConfiguracionSistema:
        ConfiguracionSistemaService._validar_acceso_empresa(db, current_user, id_empresa)
        
        config = ConfiguracionSistemaRepository.obtener_por_empresa(db, id_empresa)
        if not config:
            config = ConfiguracionSistemaRepository.crear_valores_defecto(db, id_empresa)
            db.commit()
            db.refresh(config)
            
        return config

    @staticmethod
    def actualizar_configuracion(db: Session, current_user: Usuario, id_empresa: int, datos: dict) -> ConfiguracionSistema:
        ConfiguracionSistemaService._validar_acceso_empresa(db, current_user, id_empresa)
        
        config = ConfiguracionSistemaRepository.obtener_por_empresa(db, id_empresa)
        if not config:
            config = ConfiguracionSistemaRepository.crear_valores_defecto(db, id_empresa)
            
        config = ConfiguracionSistemaRepository.actualizar(db, config, datos)
        db.commit()
        db.refresh(config)
        return config
