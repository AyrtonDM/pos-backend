from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.empresas import Empresa
from app.models.usuarios import Usuario
from app.schemas.reporte_schema import (
    DetalleVentasEmpresaResponse,
    EstadoInventarioEmpresaResponse,
    MovimientosCajaEmpresaResponse,
    MovimientosInventarioEmpresaResponse,
    PlantillaReporte,
    ReporteInventarioParametrizadoRequest,
    ReporteInventarioParametrizadoResponse,
    ReporteCajasParametrizadoRequest,
    ReporteCajasParametrizadoResponse,
    ReporteVentasParametrizadoRequest,
    ReporteVentasParametrizadoResponse,
    ResumenCajasEmpresaResponse,
    ResumenVentasEmpresaResponse,
    RespuestaInterpretacion,
    RespuestaReporte,
    SolicitudReporte,
)
from app.services.reportes_service import ReportesService
from app.services.bitacora_service import registrar_accion

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/plantillas", response_model=list[PlantillaReporte])
@router.get("/templates", response_model=list[PlantillaReporte])
def listar_plantillas(_: Usuario = Depends(get_current_user)):
    return ReportesService.obtener_catalogo()


@router.get("/{empresa_id}/resumenventas", response_model=ResumenVentasEmpresaResponse)
def obtener_resumen_ventas(
    empresa_id: int,
    fecha: date | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ReportesService.obtener_resumen_ventas_empresa(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
            fecha_reporte=fecha,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el resumen de ventas: {exc}") from exc


@router.get("/{empresa_id}/detallesventas", response_model=DetalleVentasEmpresaResponse)
def obtener_detalle_ventas(
    empresa_id: int,
    fecha: date | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ReportesService.obtener_detalle_ventas_empresa(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
            fecha_reporte=fecha,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el detalle de ventas: {exc}") from exc


@router.get("/{empresa_id}/estadoinventario", response_model=EstadoInventarioEmpresaResponse)
def obtener_estado_inventario(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ReportesService.obtener_estado_inventario_empresa(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el estado de inventario: {exc}") from exc


@router.get("/{empresa_id}/movimientosinventario", response_model=MovimientosInventarioEmpresaResponse)
def obtener_movimientos_inventario(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ReportesService.obtener_movimientos_inventario_empresa(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener los movimientos de inventario: {exc}") from exc


@router.get("/{empresa_id}/resumencajas", response_model=ResumenCajasEmpresaResponse)
def obtener_resumen_cajas(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ReportesService.obtener_resumen_cajas_empresa(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el resumen de cajas: {exc}") from exc


@router.get("/{empresa_id}/movimientoscaja", response_model=MovimientosCajaEmpresaResponse)
def obtener_movimientos_caja(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ReportesService.obtener_movimientos_caja_empresa(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener los movimientos de caja: {exc}") from exc


@router.post("/{empresa_id}/ventasparametrizado", response_model=ReporteVentasParametrizadoResponse)
def obtener_reporte_ventas_parametrizado(
    empresa_id: int,
    filtros: ReporteVentasParametrizadoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = ReportesService.obtener_reporte_ventas_parametrizado(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
            filtros=filtros,
        )
        try:
            registrar_accion(
                usuario_nombre=current_user.email if current_user else "UsuarioDesconocido",
                accion="Generó reporte de ventas",
                empresa_nombre=str(empresa_id)
            )
        except Exception:
            pass
        return resultado
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el reporte de ventas: {exc}") from exc


@router.post("/{empresa_id}/inventarioparametrizado", response_model=ReporteInventarioParametrizadoResponse)
def obtener_reporte_inventario_parametrizado(
    empresa_id: int,
    filtros: ReporteInventarioParametrizadoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = ReportesService.obtener_reporte_inventario_parametrizado(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
            filtros=filtros,
        )
        try:
            registrar_accion(
                usuario_nombre=current_user.email if current_user else "UsuarioDesconocido",
                accion="Generó reporte de inventario",
                empresa_nombre=str(empresa_id)
            )
        except Exception:
            pass
        return resultado
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el reporte de inventario: {exc}") from exc


@router.post("/{empresa_id}/cajasparametrizado", response_model=ReporteCajasParametrizadoResponse)
def obtener_reporte_cajas_parametrizado(
    empresa_id: int,
    filtros: ReporteCajasParametrizadoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = ReportesService.obtener_reporte_cajas_parametrizado(
            db=db,
            current_user=current_user,
            empresa_id=empresa_id,
            filtros=filtros,
        )
        try:
            registrar_accion(
                usuario_nombre=current_user.email if current_user else "UsuarioDesconocido",
                accion="Generó reporte de cajas",
                empresa_nombre=str(empresa_id)
            )
        except Exception:
            pass
        return resultado
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el reporte de cajas: {exc}") from exc


@router.post("/{empresa_id}/interpretar", response_model=RespuestaInterpretacion)
@router.post("/{empresa_id}/interpret", response_model=RespuestaInterpretacion)
def interpretar_reporte(
    empresa_id: int,
    solicitud: SolicitudReporte,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id_empresa == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="La empresa no existe.")

    especificacion, advertencias = ReportesService.interpretar_solicitud(solicitud)
    plantilla = next(
        (item for item in ReportesService.obtener_catalogo() if item.identificador == especificacion.identificador_plantilla),
        None,
    )
    return RespuestaInterpretacion(
        especificacion=especificacion,
        plantilla=plantilla,
        advertencias=advertencias,
    )


@router.post("/{empresa_id}/ejecutar", response_model=RespuestaReporte)
@router.post("/{empresa_id}/run", response_model=RespuestaReporte)
def ejecutar_reporte(
    empresa_id: int,
    solicitud: SolicitudReporte,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id_empresa == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="La empresa no existe.")

    try:
        resultado = ReportesService.ejecutar_reporte(db=db, solicitud=solicitud, empresa_id=empresa_id)
        try:
            registrar_accion(
                usuario_nombre=current_user.email if current_user else "UsuarioDesconocido",
                accion="Ejecutó reporte interpretado",
                empresa_nombre=str(empresa_id)
            )
        except Exception:
            pass
        return resultado
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el reporte: {exc}") from exc
