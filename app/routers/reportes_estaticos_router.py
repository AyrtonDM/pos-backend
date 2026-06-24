from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.empresas.caja import Caja
from app.models.empresas.caja_sesion import CajaSesion
from app.models.empresas.movimiento_caja import MovimientoCaja
from app.models.inventario.stock import Stock
from app.models.inventario.movimiento_inventario import MovimientoInventario
from app.models.ventas.venta import Venta
from app.models.empresas.sucursal import Sucursal
from app.models.usuarios.usuario import Usuario
from app.schemas.estaticos_schema import (
    CajaResumen,
    InventarioResumenItem,
    MovimientoCajaItem,
    MovimientoInventarioItem,
    VentaDetalleItem,
    VentaResumen,
)

router = APIRouter(prefix="/api/v1/reportes/estaticos", tags=["reportes_estaticos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _is_admin(usuario: Usuario, empresa_id: int) -> bool:
    for ur in usuario.usuario_roles:
        if ur.id_empresa == empresa_id and ur.rol and getattr(ur.rol, 'nombre', '').lower() == 'administrador':
            return True
    return False


@router.get("/{empresa_id}/caja/resumen", response_model=List[CajaResumen])
def caja_resumen(
    empresa_id: int,
    date: datetime | None = Query(None, description="Fecha para el resumen (ISO date). Si se omite se usa hoy)."),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_admin(usuario, empresa_id):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    target = date or datetime.utcnow()
    inicio = datetime.combine(target.date(), datetime.min.time())
    fin = datetime.combine(target.date(), datetime.max.time())

    sucursales = db.query(Sucursal).filter(Sucursal.id_empresa == empresa_id).all()
    resultados: list[CajaResumen] = []

    for s in sucursales:
        cajas = db.query(Caja).filter(Caja.id_sucursal == s.id_sucursal).all()
        for c in cajas:
            sesiones = (
                db.query(CajaSesion)
                .filter(CajaSesion.id_caja == c.id_caja)
                .filter(CajaSesion.fecha_apertura >= inicio)
                .filter(CajaSesion.fecha_apertura <= fin)
                .all()
            )

            monto_inicial = 0.0
            total_ingresos = 0.0
            total_egresos = 0.0

            for ses in sesiones:
                monto_inicial += float(ses.monto_inicial or 0)
                movimientos = db.query(MovimientoCaja).filter(MovimientoCaja.id_caja_sesion == ses.id_caja_sesion).all()
                for m in movimientos:
                    nombre_tipo = getattr(m.tipo_movimiento_caja, 'nombre', '') if m.tipo_movimiento_caja else ''
                    if 'ingreso' in nombre_tipo.lower() or 'entrada' in nombre_tipo.lower():
                        total_ingresos += float(m.monto or 0)
                    else:
                        total_egresos += float(m.monto or 0)

            diferencia = total_ingresos - total_egresos

            resultados.append(CajaResumen(
                id_sucursal=s.id_sucursal,
                id_caja=c.id_caja,
                monto_inicial=round(monto_inicial, 2),
                total_ingresos=round(total_ingresos, 2),
                total_egresos=round(total_egresos, 2),
                diferencia=round(diferencia, 2),
            ))

    return resultados


@router.get("/{empresa_id}/caja/detalle", response_model=List[MovimientoCajaItem])
def caja_detalle(
    empresa_id: int,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_admin(usuario, empresa_id):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    fin = end or datetime.utcnow()
    inicio = start or (fin - timedelta(days=1))

    movimientos = (
        db.query(MovimientoCaja)
        .join(CajaSesion)
        .join(Caja)
        .join(Sucursal)
        .filter(Sucursal.id_empresa == empresa_id)
        .filter(MovimientoCaja.fecha >= inicio)
        .filter(MovimientoCaja.fecha <= fin)
        .order_by(CajaSesion.id_caja_sesion.asc(), MovimientoCaja.fecha.asc())
        .all()
    )

    return [
        MovimientoCajaItem(
            id_movimiento_caja=m.id_movimiento_caja,
            id_caja_sesion=m.id_caja_sesion,
            id_caja=m.caja_sesion.id_caja if m.caja_sesion else None,
            fecha=m.fecha,
            monto=float(m.monto or 0),
            concepto=m.concepto,
            tipo_movimiento=getattr(m.tipo_movimiento_caja, 'nombre', None) if m.tipo_movimiento_caja else None,
        )
        for m in movimientos
    ]


@router.get("/{empresa_id}/inventario/resumen", response_model=List[InventarioResumenItem])
def inventario_resumen(
    empresa_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_admin(usuario, empresa_id):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    stocks = (
        db.query(Stock)
        .join(Sucursal)
        .filter(Sucursal.id_empresa == empresa_id)
        .all()
    )

    agregados: dict[int, dict] = {}
    for s in stocks:
        pid = s.id_producto
        if pid not in agregados:
            agregados[pid] = {"nombre": getattr(s.producto, 'nombre', ''), "total": 0}
        agregados[pid]['total'] += int(s.cantidad or 0)

    return [
        InventarioResumenItem(id_producto=pid, nombre_producto=data['nombre'], total_stock=data['total'])
        for pid, data in agregados.items()
    ]


@router.get("/{empresa_id}/inventario/detalle", response_model=List[MovimientoInventarioItem])
def inventario_detalle(
    empresa_id: int,
    days: int = Query(7, description="Dias hacia atras a incluir"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_admin(usuario, empresa_id):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    inicio = datetime.utcnow() - timedelta(days=days)

    movimientos = (
        db.query(MovimientoInventario)
        .join(Sucursal)
        .filter(Sucursal.id_empresa == empresa_id)
        .filter(MovimientoInventario.fecha_movimiento >= inicio)
        .order_by(MovimientoInventario.fecha_movimiento.desc())
        .all()
    )

    return [
        MovimientoInventarioItem(
            id_movimiento_inventario=m.id_movimiento_inventario,
            id_producto=m.id_producto,
            cantidad=int(m.cantidad),
            fecha_movimiento=m.fecha_movimiento,
            observacion=m.observacion,
        )
        for m in movimientos
    ]


@router.get("/{empresa_id}/ventas/resumen", response_model=List[VentaResumen])
def ventas_resumen(
    empresa_id: int,
    date: datetime | None = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_admin(usuario, empresa_id):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    target = date or datetime.utcnow()
    inicio = datetime.combine(target.date(), datetime.min.time())
    fin = datetime.combine(target.date(), datetime.max.time())

    ventas = (
        db.query(Venta)
        .join(CajaSesion)
        .join(Sucursal)
        .filter(Sucursal.id_empresa == empresa_id)
        .filter(Venta.fecha >= inicio)
        .filter(Venta.fecha <= fin)
        .all()
    )

    agrupado: dict[int, dict] = {}
    for v in ventas:
        sid = v.caja_sesion.id_caja if v.caja_sesion else 0
        if sid not in agrupado:
            agrupado[sid] = {"total": 0.0, "count": 0}
        agrupado[sid]['total'] += float(v.total or 0)
        agrupado[sid]['count'] += 1

    return [VentaResumen(id_sucursal=k, total_ventas=round(v['total'], 2), cantidad_ventas=v['count']) for k, v in agrupado.items()]


@router.get("/{empresa_id}/ventas/detalle", response_model=List[VentaDetalleItem])
def ventas_detalle(
    empresa_id: int,
    date: datetime | None = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_admin(usuario, empresa_id):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    target = date or datetime.utcnow()
    inicio = datetime.combine(target.date(), datetime.min.time())
    fin = datetime.combine(target.date(), datetime.max.time())

    ventas = (
        db.query(Venta)
        .join(CajaSesion)
        .join(Sucursal)
        .filter(Sucursal.id_empresa == empresa_id)
        .filter(Venta.fecha >= inicio)
        .filter(Venta.fecha <= fin)
        .order_by(Venta.fecha.desc())
        .all()
    )

    return [
        VentaDetalleItem(
            id_venta=v.id_venta,
            fecha=v.fecha,
            total=float(v.total or 0),
            id_caja_sesion=v.id_caja_sesion,
            id_usuario=v.id_usuario,
        )
        for v in ventas
    ]
