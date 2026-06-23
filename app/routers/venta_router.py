from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ventas import MetodoPago, TipoVenta
from app.schemas.venta_schema import MetodoPagoResponse, TipoVentaResponse
from app.schemas.venta_schema import VentaCreate, VentaResponse
from app.core.security import get_current_user
from app.services.venta_service import VentaService
from app.services.bitacora_service import registrar_accion
from fastapi import Depends
from app.models.usuarios.usuario import Usuario

venta_router = APIRouter(prefix="/api/ventas", tags=["ventas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        try:
            db.rollback()
        except OperationalError:
            db.invalidate()
        raise
    finally:
        try:
            db.close()
        except OperationalError:
            db.invalidate()


@venta_router.get("/tipos-venta", response_model=list[TipoVentaResponse])
def listar_tipos_venta(db: Session = Depends(get_db)):
    try:
        tipos = (
            db.query(TipoVenta)
            .order_by(TipoVenta.id_tipo_venta.asc())
            .all()
        )
        return tipos
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar tipos de venta.")


@venta_router.get("/metodos-pago", response_model=list[MetodoPagoResponse])
def listar_metodos_pago(db: Session = Depends(get_db)):
    try:
        metodos = (
            db.query(MetodoPago)
            .order_by(MetodoPago.id_metodo_pago.asc())
            .all()
        )
        return metodos
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar metodos de pago.")



@venta_router.post("/sesiones/{id_caja_sesion}/ventas", response_model=VentaResponse)
def crear_venta(id_caja_sesion: int, datos: VentaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    resultado = VentaService.crear_venta_completa(db=db, current_user=current_user, id_caja_sesion=id_caja_sesion, payload=datos)
    
    # Registrar en bitácora
    try:
        usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
        venta_obj = resultado["venta"]
        registrar_accion(
            usuario_nombre=usuario_nombre,
            accion=f"Registró venta ID: {venta_obj.id_venta}, total: {venta_obj.total}"
        )
    except Exception:
        # Si falla la bitácora, no afectar la venta
        pass
    
    return resultado["venta"]


@venta_router.get("/sesiones/{id_caja_sesion}/ventas", response_model=list[VentaResponse])
def historial_ventas(id_caja_sesion: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        ventas = VentaService.obtener_historial_por_caja_sesion(db=db, current_user=current_user, id_caja_sesion=id_caja_sesion)
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            registrar_accion(
                usuario_nombre=usuario_nombre,
                accion="Ingresó al módulo de ventas"
            )
        except Exception:
            pass
        return ventas
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener historial de ventas.")
