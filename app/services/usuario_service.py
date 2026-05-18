# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.repositories.usuario_repository import UsuarioRepository
from app.core.security import (
    create_access_token,
    generate_temporary_password,
    generate_verification_code,
    get_password_hash,
    hash_verification_code,
    verify_password,
)
from app.utils.email_service import send_password_recovery_email, send_verification_email

load_dotenv()


class UsuarioService:
    PASSWORD_RECOVERY_MESSAGE = (
        "Si el correo esta registrado, recibiras una nueva contrasena en tu email."
    )

    @staticmethod
    def registrar_usuario(
        db: Session,
        email: str,
        contrasena: str,
        nombre_completo: str,
        fecha_nacimiento,
        genero: str,
        telefono: str,
        documento: str,
    ) -> dict:
        """
        Registra un nuevo usuario:
        1. Verifica que no exista otro usuario con el mismo email
        2. Crea la persona y usuario
        3. Genera codigo de verificacion
        4. Envia email con el codigo
        """
        # Verificar que el email no exista
        usuario_existente = UsuarioRepository.obtener_usuario_por_email(db, email)
        if usuario_existente:
            raise ValueError("El correo electronico ya esta registrado.")

        # Hash la contrasena
        contrasena_hash = get_password_hash(contrasena)

        # Crear usuario y persona
        usuario = UsuarioRepository.crear_usuario_con_persona(
            db=db,
            email=email,
            contrasena_hash=contrasena_hash,
            nombre_completo=nombre_completo,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            telefono=telefono,
            documento=documento,
        )

        # Generar codigo de verificacion
        codigo = generate_verification_code(length=6)
        codigo_hash = hash_verification_code(codigo)
        expiration_minutes = int(os.getenv("VERIFICATION_CODE_EXPIRATION_MINUTES", "15"))
        expira_en = datetime.utcnow() + timedelta(
            minutes=expiration_minutes
        )

        # Actualizar usuario con codigo de verificacion
        UsuarioRepository.actualizar_codigo_verificacion(
            db=db,
            usuario_id=usuario.id_usuario,
            codigo_hash=codigo_hash,
            expira_en=expira_en,
        )

        # Enviar email con codigo
        email_enviado = send_verification_email(
            email=email,
            nombre=nombre_completo,
            codigo_verificacion=codigo,
        )

        return {
            "usuario_id": usuario.id_usuario,
            "email": usuario.email,
            "activo": usuario.activo,
            "mensaje": "Registro exitoso. Por favor verifica tu correo para activar tu cuenta.",
            "email_enviado": email_enviado,
        }

    @staticmethod
    def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
        """Verifica una contrasena contra su hash."""
        return verify_password(contrasena_plana, contrasena_hash)

    @staticmethod
    def login_usuario(db: Session, email: str, contrasena: str) -> dict:
        """
        Autentica un usuario y retorna un token JWT.
        """
        usuario = UsuarioRepository.obtener_usuario_por_email(db, email)
        if not usuario:
            raise ValueError("Correo o contrasena incorrectos.")

        if not verify_password(contrasena, usuario.contrasena):
            raise ValueError("Correo o contrasena incorrectos.")

        if not usuario.activo:
            raise ValueError("Usuario no encontrado o inactivo")

        # collect roles from usuario.usuario_roles relationship
        roles = []
        try:
            for ur in usuario.usuario_roles:
                if ur.rol and getattr(ur.rol, 'nombre', None):
                    roles.append(ur.rol.nombre)
        except Exception:
            roles = []

        token = create_access_token(user_id=usuario.id_usuario, email=usuario.email, roles=roles)
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    @staticmethod
    def verificar_codigo(db: Session, email: str, codigo: str) -> dict:
        """
        Verifica el codigo enviado al correo y activa el usuario.
        """
        usuario = UsuarioRepository.obtener_usuario_por_email(db, email)
        if not usuario:
            raise ValueError("No existe un usuario con ese correo.")

        if usuario.activo:
            return {
                "email": usuario.email,
                "activo": usuario.activo,
                "mensaje": "La cuenta ya esta activa.",
            }

        if not usuario.codigo_verificacion_hash or not usuario.codigo_verificacion_expira_en:
            raise ValueError("No hay un codigo de verificacion pendiente para este usuario.")

        max_attempts = int(os.getenv("VERIFICATION_CODE_MAX_ATTEMPTS", "3"))
        if usuario.codigo_verificacion_intentos >= max_attempts:
            raise ValueError("Superaste el maximo de intentos. Solicita un nuevo codigo.")

        if datetime.utcnow() > usuario.codigo_verificacion_expira_en:
            raise ValueError("El codigo de verificacion ha expirado. Solicita uno nuevo.")

        codigo_hash = hash_verification_code(codigo)
        if codigo_hash != usuario.codigo_verificacion_hash:
            usuario = UsuarioRepository.incrementar_intentos_verificacion(db, usuario)
            intentos_restantes = max_attempts - usuario.codigo_verificacion_intentos
            if intentos_restantes <= 0:
                raise ValueError("Superaste el maximo de intentos. Solicita un nuevo codigo.")
            raise ValueError(
                f"Codigo incorrecto. Te quedan {intentos_restantes} intento(s)."
            )

        usuario = UsuarioRepository.activar_usuario_y_limpiar_verificacion(db, usuario)
        return {
            "email": usuario.email,
            "activo": usuario.activo,
            "mensaje": "Cuenta verificada y activada correctamente.",
        }

    @staticmethod
    def solicitar_recuperacion_contrasena(db: Session, email: str) -> dict:
        """
        Genera y envia una nueva contrasena si el usuario existe.
        La respuesta publica siempre es generica para no filtrar emails registrados.
        """
        usuario = UsuarioRepository.obtener_usuario_por_email(db, email)
        if not usuario:
            return {"mensaje": UsuarioService.PASSWORD_RECOVERY_MESSAGE}

        nueva_contrasena = generate_temporary_password()
        nombre = usuario.persona.nombre_completo if usuario.persona else usuario.email

        email_enviado = send_password_recovery_email(
            email=usuario.email,
            nombre=nombre,
            nueva_contrasena=nueva_contrasena,
        )

        if email_enviado:
            UsuarioRepository.actualizar_contrasena(
                db=db,
                usuario=usuario,
                contrasena_hash=get_password_hash(nueva_contrasena),
            )

        return {"mensaje": UsuarioService.PASSWORD_RECOVERY_MESSAGE}
