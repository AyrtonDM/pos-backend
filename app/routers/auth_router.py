# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.usuario_schema import UsuarioRegister, UsuarioVerifyCode
from app.services.usuario_service import UsuarioService

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
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al registrar el usuario.")


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
