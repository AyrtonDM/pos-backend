# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.sucursal_schema import (
    EmpleadoSucursalResponse,
    InvitacionEmpleadoCreate,
    SucursalEmpleadoAsignadaResponse,
    SucursalCreate,
    SucursalResponse,
    SucursalUpdate,
)
from app.services.sucursal_service import SucursalService

empresa_router = APIRouter(prefix="/api/empresas", tags=["sucursales"])
sucursal_router = APIRouter(prefix="/api/sucursales", tags=["sucursales"])
invitacion_router = APIRouter(prefix="/api/invitaciones", tags=["invitaciones"])


def _render_invitacion_aceptada_html(
    nombre_empresa: str,
    nombre_sucursal: str,
    ya_aceptada: bool = False,
) -> str:
    titulo = "Invitacion aceptada" if not ya_aceptada else "Invitacion ya aceptada"
    subtitulo = (
        "Ahora eres trabajador de la empresa"
        if not ya_aceptada
        else "Ya formas parte de la empresa"
    )
    mensaje_detalle = (
        "Tu acceso como trabajador ya quedo habilitado. Cuando quieras continuar, "
        "puedes volver a la aplicacion e ingresar con tu cuenta."
        if not ya_aceptada
        else "Este enlace ya habia sido utilizado antes, pero tu acceso sigue activo "
        "para esta empresa y sucursal."
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{titulo}</title>
    <style>
        :root {{
            --color-bg: #c7dd72;
            --color-bg-soft: #d8e89a;
            --color-surface: #ffffff;
            --color-primary: #f4a62a;
            --color-primary-hover: #de931d;
            --color-text: #2d2d2d;
            --color-text-soft: #6b7280;
            --color-border: #e5e7eb;
            --color-success: #22c55e;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: var(--color-text);
            background:
                radial-gradient(circle at top left, rgba(255,255,255,0.55), transparent 35%),
                linear-gradient(135deg, var(--color-bg-soft), var(--color-bg));
        }}

        .card {{
            width: 100%;
            max-width: 720px;
            background: var(--color-surface);
            border: 1px solid rgba(255,255,255,0.55);
            border-radius: 28px;
            padding: 40px 36px;
            box-shadow: 0 24px 60px rgba(45, 45, 45, 0.16);
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: "";
            position: absolute;
            inset: 0 0 auto auto;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(244,166,42,0.28), transparent 70%);
            transform: translate(30%, -30%);
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            border-radius: 999px;
            background: rgba(34, 197, 94, 0.12);
            color: #15803d;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}

        .badge-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--color-success);
        }}

        h1 {{
            margin: 22px 0 14px;
            font-size: clamp(2rem, 4vw, 3.2rem);
            line-height: 1.02;
        }}

        p {{
            margin: 0;
            font-size: 1.05rem;
            line-height: 1.7;
            color: var(--color-text-soft);
        }}

        .highlight {{
            margin-top: 28px;
            padding: 22px;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(244,166,42,0.15), rgba(199,221,114,0.26));
            border: 1px solid var(--color-border);
        }}

        .highlight strong {{
            color: var(--color-text);
        }}

        .footer {{
            margin-top: 24px;
            font-size: 0.95rem;
            color: var(--color-text-soft);
        }}

        @media (max-width: 640px) {{
            .card {{
                padding: 28px 22px;
                border-radius: 22px;
            }}
        }}
    </style>
</head>
<body>
    <main class="card">
        <div class="badge">
            <span class="badge-dot"></span>
            {titulo}
        </div>
        <h1>{titulo}</h1>
        <p>
            {subtitulo} <strong>{nombre_empresa}</strong> en la sucursal
            <strong>{nombre_sucursal}</strong>.
        </p>
        <section class="highlight">
            <p>
                {mensaje_detalle}
            </p>
        </section>
        <p class="footer">Gracias por unirte al equipo.</p>
    </main>
</body>
</html>"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@empresa_router.post("/{id_empresa}/sucursales", response_model=SucursalResponse)
def crear_sucursal(
    id_empresa: int,
    datos: SucursalCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.crear_sucursal_para_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la sucursal.")


@empresa_router.get("/{id_empresa}/sucursales", response_model=list[SucursalResponse])
def obtener_sucursales(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursales_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las sucursales.")


@empresa_router.get(
    "/{id_empresa}/sucursales/{id_sucursal}",
    response_model=SucursalResponse,
)
def obtener_sucursal(
    id_empresa: int,
    id_sucursal: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursal_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la sucursal.")


@empresa_router.post("/{id_empresa}/sucursales/{id_sucursal}/invitar-empleado")
def invitar_empleado(
    id_empresa: int,
    id_sucursal: int,
    datos: InvitacionEmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.enviar_invitacion_empleado(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            email=datos.email,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al enviar la invitacion.")


@empresa_router.get(
    "/{id_empresa}/sucursales/{id_sucursal}/empleados",
    response_model=list[EmpleadoSucursalResponse],
)
def obtener_empleados_sucursal(
    id_empresa: int,
    id_sucursal: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_empleados_de_sucursal(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los empleados.")


@sucursal_router.put("/{id_sucursal}", response_model=SucursalResponse)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.actualizar_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_sucursal=id_sucursal,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la sucursal.")


@sucursal_router.get(
    "/mis-sucursales-empleado",
    response_model=list[SucursalEmpleadoAsignadaResponse],
)
def obtener_mis_sucursales_empleado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursales_asignadas_como_empleado(
            db=db,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las sucursales.")


@invitacion_router.get(
    "/empleado/aceptar/{id_empresa}/{id_sucursal}/{id_usuario}",
    response_class=HTMLResponse,
)
def aceptar_invitacion_empleado(
    id_empresa: int,
    id_sucursal: int,
    id_usuario: int,
    db: Session = Depends(get_db),
):
    try:
        resultado = SucursalService.aceptar_invitacion_empleado(
            db=db,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_usuario=id_usuario,
        )
        return HTMLResponse(
            content=_render_invitacion_aceptada_html(
                nombre_empresa=resultado.get("empresa", ""),
                nombre_sucursal=resultado.get("sucursal", ""),
                ya_aceptada=resultado.get("ya_aceptada", False),
            )
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al aceptar la invitacion.")
