# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
import logging
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.models.empresas import Empresa
from app.schemas.caja_schema import (
    CajaCierreDetalleCreate,
    CajaSesionCierreResponse,
    CajaCreate,
    CajaResponse,
    CajaSesionCreate,
    CajaSesionResponse,
    CajaUpdate,
    ResumenMovimientosCajaResponse,
)
from app.schemas.movimiento_caja_schema import (
    MovimientoCajaCreate,
    MovimientoCajaResponse,
)
from app.schemas.sucursal_schema import (
    ClienteEmpresaResponse,
    EditarPersonalCreate,
    InvitacionClienteCreate,
    InvitacionEmpleadoCreate,
    PersonalEmpresaAgrupadoResponse,
    PersonalEmpresaResponse,
    SucursalEmpleadoAsignadaResponse,
    SucursalCreate,
    SucursalResponse,
    SucursalUpdate,
)
from app.services.caja_service import CajaService, CajaSesionAbiertaError
from app.services.sucursal_service import SucursalService
from app.services.bitacora_service import registrar_accion

empresa_router = APIRouter(prefix="/api/empresas", tags=["sucursales"])
sucursal_router = APIRouter(prefix="/api/sucursales", tags=["sucursales"])
caja_router = APIRouter(prefix="/api/cajas", tags=["cajas"])
invitacion_router = APIRouter(prefix="/api/invitaciones", tags=["invitaciones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _render_client_invitation_html(
    mensaje: str,
    empresa_nombre: str,
    es_error: bool = False,
) -> str:
    color_principal = "#d9534f" if es_error else "#007bff"
    titulo = "Invitacion de cliente" if not es_error else "No se pudo completar la invitacion"
    badge = "?" if es_error else "?"
    empresa_bloque = (
        f'<p style="color: #666; font-size: 14px; line-height: 1.7; margin: 0 0 24px 0;">Empresa: <strong>{empresa_nombre}</strong></p>'
        if empresa_nombre
        else ""
    )
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; margin: 0;">
            <div style="background-color: white; padding: 24px; border-radius: 8px; max-width: 640px; margin: 0 auto; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);">
                <div style="width: 56px; height: 56px; border-radius: 50%; background-color: {color_principal}; color: white; display: flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 18px;">
                    {badge}
                </div>
                <h2 style="color: #333; margin: 0 0 12px 0;">{titulo}</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.7; margin: 0 0 12px 0;">{mensaje}</p>
                {empresa_bloque}
                <div style="padding-top: 12px; border-top: 1px solid #eee; color: #999; font-size: 12px; line-height: 1.6;">
                    Esta confirmacion fue generada automaticamente al abrir el enlace de invitacion.
                </div>
            </div>
        </body>
    </html>
    """


@empresa_router.post("/{id_empresa}/sucursales", response_model=SucursalResponse)
def crear_sucursal(
    id_empresa: int,
    datos: SucursalCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = SucursalService.crear_sucursal_para_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
        )
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            
            empresa = db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
            empresa_nombre = empresa.nombre if empresa else None
            sucursal_nombre = resultado.nombre if resultado and hasattr(resultado, 'nombre') else datos.nombre

            registrar_accion(
                usuario_nombre=usuario_nombre,
                empresa_nombre=empresa_nombre,
                sucursal_nombre=sucursal_nombre,
                accion=f"Registró la sucursal: {sucursal_nombre}"
            )
        except Exception:
            pass
        return resultado
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


@empresa_router.post("/{id_empresa}/invitar-empleado")
def invitar_empleado(
    id_empresa: int,
    datos: InvitacionEmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.enviar_invitacion_empleado(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            email=datos.email,
            id_sucursales=datos.id_sucursales,
            id_rol=datos.id_rol,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al enviar la invitacion.")


@empresa_router.post("/{id_empresa}/invitar-cliente")
def invitar_cliente(
    id_empresa: int,
    datos: InvitacionClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.enviar_invitacion_cliente(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            email=datos.email,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al enviar la invitacion.")


@empresa_router.get(
    "/{id_empresa}/personal",
    response_model=list[PersonalEmpresaAgrupadoResponse],
)
def obtener_personal_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_personal_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el personal.")


@empresa_router.put(
    "/{id_empresa}/editarpersonal",
    response_model=list[PersonalEmpresaResponse],
)
def editar_personal_empresa(
    id_empresa: int,
    datos: EditarPersonalCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.editar_personal_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            email=datos.email,
            id_sucursales=datos.id_sucursales,
            id_rol=datos.id_rol,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al editar el personal.")


@empresa_router.get(
    "/{id_empresa}/clientes",
    response_model=list[ClienteEmpresaResponse],
)
def obtener_clientes_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_clientes_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los clientes.")


@sucursal_router.post("/{id_sucursal}/cajas", response_model=CajaResponse)
def crear_caja(
    id_sucursal: int,
    datos: CajaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.crear_caja(
            db=db,
            current_user=current_user,
            id_sucursal=id_sucursal,
            nombre=datos.nombre,
            codigo=datos.codigo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la caja.")


@caja_router.post(
    "/{id_caja}/sesiones",
    response_model=CajaSesionResponse,
)
def crear_caja_sesion(
    id_caja: int,
    datos: CajaSesionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.crear_caja_sesion(
            db=db,
            current_user=current_user,
            id_caja=id_caja,
            monto_inicial=datos.monto_inicial,
            nota=datos.nota,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CajaSesionAbiertaError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "id_caja": e.id_caja,
                "id_caja_sesion": e.id_caja_sesion,
                "detail": e.message,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la sesion de caja.")


@caja_router.post(
    "/sesiones/{id_caja_sesion}/movimientos",
    response_model=MovimientoCajaResponse,
)
def crear_movimiento_caja(
    id_caja_sesion: int,
    datos: MovimientoCajaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.crear_movimiento_caja(
            db=db,
            current_user=current_user,
            id_caja_sesion=id_caja_sesion,
            concepto=datos.concepto,
            monto=datos.monto,
            id_tipo_movimiento_caja=datos.id_tipo_movimiento_caja,
            id_metodo_pago=datos.id_metodo_pago,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el movimiento de caja.")


@caja_router.get(
    "/sesiones/{id_caja_sesion}/movimientos",
    response_model=list[MovimientoCajaResponse],
)
def listar_movimientos_caja_sesion(
    id_caja_sesion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.listar_movimientos_de_caja_sesion(
            db=db,
            current_user=current_user,
            id_caja_sesion=id_caja_sesion,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar los movimientos de caja.")


@caja_router.get(
    "/sesiones/{id_caja_sesion}/movimientos/resumen",
    response_model=ResumenMovimientosCajaResponse,
)
def resumen_movimientos_caja_sesion(
    id_caja_sesion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.resumen_movimientos_por_metodo_pago(
            db=db,
            current_user=current_user,
            id_caja_sesion=id_caja_sesion,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el resumen de movimientos de caja.")


@caja_router.post(
    "/sesiones/{id_caja_sesion}/cierres",
    response_model=CajaSesionCierreResponse,
)
def cerrar_caja_sesion(
    id_caja_sesion: int,
    datos: list[CajaCierreDetalleCreate],
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.cerrar_caja_sesion_con_detalles(
            db=db,
            current_user=current_user,
            id_caja_sesion=id_caja_sesion,
            cierres=[dato.model_dump() for dato in datos],
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al cerrar la sesion de caja.")


@empresa_router.get(
    "/{id_empresa}/sucursales/{id_sucursal}/cajas",
    response_model=list[CajaResponse],
)
def listar_cajas_sucursal(
    id_empresa: int,
    id_sucursal: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.listar_cajas_de_sucursal(
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
        raise HTTPException(status_code=500, detail="Error al listar las cajas.")


@empresa_router.get(
    "/{id_empresa}/sucursales/{id_sucursal}/cajas/{id_caja}",
    response_model=CajaResponse,
)
def obtener_caja_sucursal(
    id_empresa: int,
    id_sucursal: int,
    id_caja: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.obtener_caja(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_caja=id_caja,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la caja.")


@empresa_router.put(
    "/{id_empresa}/sucursales/{id_sucursal}/cajas/{id_caja}",
    response_model=CajaResponse,
)
def actualizar_caja_sucursal(
    id_empresa: int,
    id_sucursal: int,
    id_caja: int,
    datos: CajaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return CajaService.actualizar_caja(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
            id_caja=id_caja,
            nombre=datos.nombre,
            codigo=datos.codigo,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la caja.")


@sucursal_router.put("/{id_sucursal}", response_model=SucursalResponse)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = SucursalService.actualizar_sucursal_del_usuario(
            db=db,
            current_user=current_user,
            id_sucursal=id_sucursal,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
            activo=datos.activo,
        )
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            registrar_accion(
                usuario_nombre=usuario_nombre,
                accion=f"Editó la sucursal ID: {id_sucursal}"
            )
        except Exception:
            pass
        return resultado
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la sucursal.")


@sucursal_router.get(
    "/mis-sucursales-empleado/{id_empresa}",
    response_model=list[SucursalEmpleadoAsignadaResponse],
)
def obtener_mis_sucursales_empleado(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return SucursalService.obtener_sucursales_asignadas_como_empleado(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las sucursales.")


@invitacion_router.get("/empleado/aceptar/{token}")
def aceptar_invitacion_empleado(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        return SucursalService.aceptar_invitacion_empleado(
            db=db,
            token=token,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al aceptar la invitacion.")


@invitacion_router.get("/cliente/aceptar/{id_empresa}/{id_usuario}")
def aceptar_invitacion_cliente(
    id_empresa: int,
    id_usuario: int,
    db: Session = Depends(get_db),
):
    try:
        resultado = SucursalService.aceptar_invitacion_cliente(
            db=db,
            id_empresa=id_empresa,
            id_usuario=id_usuario,
        )
        html = _render_client_invitation_html(
            mensaje=resultado["mensaje"],
            empresa_nombre=resultado["empresa_nombre"],
        )
        return HTMLResponse(content=html, status_code=200)
    except LookupError as e:
        html = _render_client_invitation_html(
            mensaje=str(e),
            empresa_nombre="",
            es_error=True,
        )
        return HTMLResponse(content=html, status_code=404)
    except ValueError as e:
        html = _render_client_invitation_html(
            mensaje=str(e),
            empresa_nombre="",
            es_error=True,
        )
        return HTMLResponse(content=html, status_code=400)
    except Exception:
        html = _render_client_invitation_html(
            mensaje="Error al aceptar la invitacion.",
            empresa_nombre="",
            es_error=True,
        )
        return HTMLResponse(content=html, status_code=500)
