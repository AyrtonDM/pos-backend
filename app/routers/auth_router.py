# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.usuario_schema import (
    TokenResponse,
    UsuarioForgotPassword,
    UsuarioLogin,
    UsuarioRegister,
    UsuarioVerifyCode,
)
from app.services.usuario_service import UsuarioService
from app.services.bitacora_service import registrar_accion

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=dict)
def registrar_usuario(
    datos: UsuarioRegister,
    db: Session = Depends(get_db),
):
    """
    Endpoint para registrar un nuevo usuario.
    
    - Crea una nueva persona y usuario
    - Usuario inactivo por defecto (activo=False)
    - Genera codigo de verificacion de 6 caracteres
    - Envia el codigo al correo electronico
    
    Body:
    {
        "email": "usuario@example.com",
        "contrasena": "password123",
        "nombre_completo": "Juan Perez",
        "fecha_nacimiento": "1990-01-15",
        "genero": "M",
        "telefono": "3001234567",
        "documento": "1234567890"
    }
    """
    try:
        resultado = UsuarioService.registrar_usuario(
            db=db,
            email=datos.email,
            contrasena=datos.contrasena,
            nombre_completo=datos.nombre_completo,
            fecha_nacimiento=datos.fecha_nacimiento,
            genero=datos.genero,
            telefono=datos.telefono,
            documento=datos.documento,
        )
        # Registrar en bitácora
        try:
            registrar_accion(
                usuario_nombre=datos.nombre_completo,
                accion="Se registró el usuario"
            )
        except Exception:
            # Si falla la bitácora, no afectar el registro
            pass
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al registrar el usuario.")


@router.post("/login", response_model=TokenResponse)
def login_usuario(
    datos: UsuarioLogin,
    db: Session = Depends(get_db),
):
    """
    Login de usuario usando email y contrasena.

    Body:
    {
        "email": "usuario@example.com",
        "contrasena": "password123"
    }
    """
    try:
        resultado = UsuarioService.login_usuario(
            db=db,
            email=datos.email,
            contrasena=datos.contrasena,
        )
        # Registrar en bitácora
        try:
            registrar_accion(
                usuario_nombre=datos.email,
                accion="Inició sesión"
            )
        except Exception:
            # Si falla la bitácora, no afectar el login
            pass
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al iniciar sesion.")


@router.post("/verify-code", response_model=dict)
def verificar_codigo(
    datos: UsuarioVerifyCode,
    db: Session = Depends(get_db),
):
    """
    Valida el codigo de verificacion y activa la cuenta del usuario.

    Body:
    {
        "email": "usuario@example.com",
        "codigo": "aB3xF9"
    }
    """
    try:
        resultado = UsuarioService.verificar_codigo(
            db=db,
            email=datos.email,
            codigo=datos.codigo,
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al verificar el codigo.")


@router.post("/forgot-password", response_model=dict)
def solicitar_recuperacion_contrasena(
    datos: UsuarioForgotPassword,
    db: Session = Depends(get_db),
):
    """
    Solicita recuperacion de contrasena por email.

    Body:
    {
        "email": "usuario@example.com"
    }
    """
    try:
        return UsuarioService.solicitar_recuperacion_contrasena(
            db=db,
            email=datos.email,
        )
    except Exception:
        return {"mensaje": UsuarioService.PASSWORD_RECOVERY_MESSAGE}
