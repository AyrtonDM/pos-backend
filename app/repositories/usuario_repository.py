# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.usuarios import Usuario, Persona


class UsuarioRepository:
    @staticmethod
    def crear_usuario_con_persona(
        db: Session,
        email: str,
        contrasena_hash: str,
        nombre_completo: str,
        fecha_nacimiento,
        genero: str,
        telefono: str,
        documento: str,
    ) -> Usuario:
        """
        Crea una nueva persona y usuario asociado.
        Usuario por defecto con activo=False.
        """
        # Crear persona
        persona = Persona(
            nombre_completo=nombre_completo,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            telefono=telefono,
            documento=documento,
        )
        db.add(persona)
        db.flush()  # Para obtener el id_persona generado

        # Crear usuario
        usuario = Usuario(
            id_persona=persona.id_persona,
            email=email,
            contrasena=contrasena_hash,
            activo=False,  # Por defecto inactivo hasta verificar email
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def obtener_usuario_por_email(db: Session, email: str):
        """Obtiene un usuario por su email."""
        return db.query(Usuario).filter(Usuario.email == email).first()

    @staticmethod
    def actualizar_codigo_verificacion(
        db: Session,
        usuario_id: int,
        codigo_hash: str,
        expira_en: datetime,
    ) -> Usuario:
        """Actualiza el codigo de verificacion del usuario."""
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if usuario:
            usuario.codigo_verificacion_hash = codigo_hash
            usuario.codigo_verificacion_expira_en = expira_en
            usuario.codigo_verificacion_intentos = 0
            db.commit()
            db.refresh(usuario)
        return usuario

    @staticmethod
    def obtener_usuario_por_id(db: Session, usuario_id: int):
        """Obtiene un usuario por su ID."""
        return db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()

    @staticmethod
    def incrementar_intentos_verificacion(db: Session, usuario: Usuario) -> Usuario:
        """Incrementa el contador de intentos de verificacion."""
        usuario.codigo_verificacion_intentos += 1
        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def activar_usuario_y_limpiar_verificacion(db: Session, usuario: Usuario) -> Usuario:
        """Activa el usuario y limpia datos temporales de verificacion."""
        usuario.activo = True
        usuario.codigo_verificacion_hash = None
        usuario.codigo_verificacion_expira_en = None
        usuario.codigo_verificacion_intentos = 0
        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def actualizar_contrasena(db: Session, usuario: Usuario, contrasena_hash: str) -> Usuario:
        """Actualiza la contrasena del usuario."""
        usuario.contrasena = contrasena_hash
        db.commit()
        db.refresh(usuario)
        return usuario
