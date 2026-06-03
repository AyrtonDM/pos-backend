# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.empresas import Caja, CajaSesion, Empresa, MovimientoCaja, Sucursal, TipoMovimientoCaja
from app.models.inventario import Stock
from app.models.productos import Producto
from app.models.ventas import DetalleVenta, Venta

router = APIRouter(prefix="/ws/administrador", tags=["websockets"])

DASHBOARD_POLL_SECONDS = 5


def _normalizar_texto(valor: str | None) -> str:
    return (valor or "").strip().lower()


def _clasificar_movimiento_caja(nombre: str | None) -> str:
    normalizado = _normalizar_texto(nombre)
    if any(palabra in normalizado for palabra in ["ingreso", "entrada", "abono", "cobro", "positivo", "venta"]):
        return "ingreso"
    if any(palabra in normalizado for palabra in ["egreso", "salida", "retiro", "pago", "negativo"]):
        return "egreso"
    return "desconocido"


def _extraer_id_sucursal(mensaje: dict[str, Any] | None) -> int | None:
    if not mensaje:
        return None

    datos = mensaje.get("datos")
    if isinstance(datos, list) and datos:
        candidato = datos[0]
        if isinstance(candidato, dict):
            valor = candidato.get("id_sucursal")
            return int(valor) if valor not in (None, "", 0, "0") else None

    valor = mensaje.get("id_sucursal")
    return int(valor) if valor not in (None, "", 0, "0") else None


def _firma_dashboard(dashboard: dict[str, Any]) -> str:
    comparable = dict(dashboard)
    comparable.pop("generado_en", None)
    return json.dumps(comparable, sort_keys=True, ensure_ascii=False)


def _base_sucursales(db: Session, id_empresa: int, id_sucursal: int | None = None):
    query = db.query(Sucursal).filter(Sucursal.id_empresa == id_empresa)
    if id_sucursal is not None:
        query = query.filter(Sucursal.id_sucursal == id_sucursal)
    return query


def _obtener_dashboard(db: Session, id_empresa: int, id_sucursal: int | None = None) -> dict[str, Any]:
    empresa = db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
    if empresa is None:
        return {"error": "Empresa no encontrada.", "id_empresa": id_empresa}

    hoy = datetime.utcnow().date()
    inicio_hoy = datetime.combine(hoy, time.min)
    fin_hoy = datetime.combine(hoy, time.max)
    inicio_30_dias = datetime.combine(hoy - timedelta(days=29), time.min)

    sucursales_query = _base_sucursales(db, id_empresa=id_empresa, id_sucursal=id_sucursal)
    sucursales_ids = [fila.id_sucursal for fila in sucursales_query.all()]

    ventas_hoy_query = (
        db.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id_venta),
        )
        .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
        .join(Caja, CajaSesion.id_caja == Caja.id_caja)
        .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(Venta.fecha.between(inicio_hoy, fin_hoy))
        .filter(Venta.estado != "ANULADA")
    )
    if id_sucursal is not None:
        ventas_hoy_query = ventas_hoy_query.filter(Sucursal.id_sucursal == id_sucursal)

    monto_ventas_hoy, cantidad_ventas_hoy = ventas_hoy_query.one()
    monto_ventas_hoy = Decimal(str(monto_ventas_hoy or 0))
    cantidad_ventas_hoy = int(cantidad_ventas_hoy or 0)
    ticket_promedio = monto_ventas_hoy / cantidad_ventas_hoy if cantidad_ventas_hoy else Decimal("0")

    cajas_abiertas_query = (
        db.query(func.count(CajaSesion.id_caja_sesion))
        .join(Caja, CajaSesion.id_caja == Caja.id_caja)
        .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(CajaSesion.estado == "Abierto")
    )
    if id_sucursal is not None:
        cajas_abiertas_query = cajas_abiertas_query.filter(Sucursal.id_sucursal == id_sucursal)
    cajas_abiertas = int(cajas_abiertas_query.scalar() or 0)

    producto_estrella_query = (
        db.query(
            Producto.id_producto,
            Producto.nombre,
            func.coalesce(func.sum(DetalleVenta.cantidad), 0).label("unidades"),
        )
        .join(DetalleVenta, Producto.id_producto == DetalleVenta.id_producto)
        .join(Venta, DetalleVenta.id_venta == Venta.id_venta)
        .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
        .join(Caja, CajaSesion.id_caja == Caja.id_caja)
        .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(Venta.fecha.between(inicio_hoy, fin_hoy))
        .filter(Venta.estado != "ANULADA")
        .group_by(Producto.id_producto, Producto.nombre)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
    )
    if id_sucursal is not None:
        producto_estrella_query = producto_estrella_query.filter(Sucursal.id_sucursal == id_sucursal)
    producto_estrella = producto_estrella_query.first()

    stock_query = (
        db.query(Stock)
        .join(Sucursal, Stock.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
    )
    if id_sucursal is not None:
        stock_query = stock_query.filter(Sucursal.id_sucursal == id_sucursal)
    stocks = stock_query.all()
    productos_bajo_stock = sum(
        1
        for stock in stocks
        if stock.cantidad > 0 and stock.stock_minimo is not None and stock.cantidad < stock.stock_minimo
    )
    productos_agotados = sum(1 for stock in stocks if stock.cantidad <= 0)

    movimientos_caja_query = (
        db.query(TipoMovimientoCaja.nombre, func.coalesce(func.sum(MovimientoCaja.monto), 0))
        .join(MovimientoCaja, TipoMovimientoCaja.id_tipo_movimiento_caja == MovimientoCaja.id_tipo_movimiento_caja)
        .join(CajaSesion, MovimientoCaja.id_caja_sesion == CajaSesion.id_caja_sesion)
        .join(Caja, CajaSesion.id_caja == Caja.id_caja)
        .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(MovimientoCaja.fecha.between(inicio_hoy, fin_hoy))
        .group_by(TipoMovimientoCaja.nombre)
    )
    if id_sucursal is not None:
        movimientos_caja_query = movimientos_caja_query.filter(Sucursal.id_sucursal == id_sucursal)

    ingresos_dia = Decimal("0")
    egresos_dia = Decimal("0")
    for tipo, monto in movimientos_caja_query.all():
        clasificacion = _clasificar_movimiento_caja(tipo)
        if clasificacion == "ingreso":
            ingresos_dia += Decimal(str(monto or 0))
        elif clasificacion == "egreso":
            egresos_dia += Decimal(str(monto or 0))

    evolucion_rows = (
        db.query(
            func.date(Venta.fecha).label("fecha"),
            func.coalesce(func.sum(Venta.total), 0).label("total"),
        )
        .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
        .join(Caja, CajaSesion.id_caja == Caja.id_caja)
        .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(Venta.fecha.between(inicio_30_dias, fin_hoy))
        .filter(Venta.estado != "ANULADA")
        .filter(Sucursal.id_sucursal.in_(sucursales_ids) if sucursales_ids else False)
        .group_by(func.date(Venta.fecha))
        .order_by(func.date(Venta.fecha).asc())
        .all()
    )
    evolucion = [
        {"fecha": fila.fecha.isoformat(), "total": float(fila.total or 0)}
        for fila in evolucion_rows
    ]
    total_periodo = sum(item["total"] for item in evolucion)
    pico_diario = max((item["total"] for item in evolucion), default=0)

    ventas_sucursal_rows = (
        db.query(
            Sucursal.id_sucursal,
            Sucursal.nombre,
            func.coalesce(func.sum(Venta.total), 0).label("total"),
        )
        .join(Caja, Sucursal.id_sucursal == Caja.id_sucursal)
        .join(CajaSesion, Caja.id_caja == CajaSesion.id_caja)
        .join(Venta, CajaSesion.id_caja_sesion == Venta.id_caja_sesion)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(Venta.fecha.between(inicio_30_dias, fin_hoy))
        .filter(Venta.estado != "ANULADA")
        .group_by(Sucursal.id_sucursal, Sucursal.nombre)
        .order_by(func.sum(Venta.total).desc())
        .all()
    )
    max_sucursal = max((float(fila.total or 0) for fila in ventas_sucursal_rows), default=0)
    ventas_por_sucursal = [
        {
            "id_sucursal": int(fila.id_sucursal),
            "sucursal": fila.nombre,
            "total": float(fila.total or 0),
            "porcentaje": round((float(fila.total or 0) / max_sucursal) * 100, 2) if max_sucursal else 0,
        }
        for fila in ventas_sucursal_rows
    ]

    return {
        "empresa": {
            "id_empresa": empresa.id_empresa,
            "nombre": empresa.nombre,
        },
        "filtro": {
            "id_sucursal": id_sucursal,
            "sucursales_disponibles": [
                {"id_sucursal": sucursal.id_sucursal, "nombre": sucursal.nombre}
                for sucursal in db.query(Sucursal).filter(Sucursal.id_empresa == id_empresa).order_by(Sucursal.nombre.asc()).all()
            ],
        },
        "indicadores": {
            "ventas_hoy": float(monto_ventas_hoy),
            "ticket_promedio": float(round(ticket_promedio, 2)),
            "cajas_abiertas": cajas_abiertas,
            "producto_estrella": {
                "id_producto": int(producto_estrella.id_producto),
                "nombre": producto_estrella.nombre,
                "unidades": int(producto_estrella.unidades or 0),
            } if producto_estrella else None,
            "productos_bajo_stock": productos_bajo_stock,
            "productos_agotados": productos_agotados,
            "ingresos_dia": float(ingresos_dia),
            "egresos_dia": float(egresos_dia),
            "flujo_neto": float(ingresos_dia - egresos_dia),
        },
        "evolucion_ventas_30_dias": {
            "total_periodo": round(total_periodo, 2),
            "pico_diario": round(pico_diario, 2),
            "puntos": evolucion,
        },
        "ventas_por_sucursal": ventas_por_sucursal,
        "generado_en": datetime.utcnow().isoformat(),
    }


@router.websocket("/{id_empresa}")
async def administrador_dashboard(websocket: WebSocket, id_empresa: int):
    await websocket.accept()
    db = SessionLocal()
    try:
        id_sucursal_actual: int | None = None
        dashboard = _obtener_dashboard(db=db, id_empresa=id_empresa)
        firma_dashboard = _firma_dashboard(dashboard)
        await websocket.send_json({"tipo": "dashboard", "datos": [dashboard]})

        while True:
            try:
                mensaje = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=DASHBOARD_POLL_SECONDS,
                )
                tipo = mensaje.get("tipo")
                if tipo == "dashboard":
                    id_sucursal_actual = _extraer_id_sucursal(mensaje)
                    dashboard = _obtener_dashboard(
                        db=db,
                        id_empresa=id_empresa,
                        id_sucursal=id_sucursal_actual,
                    )
                    firma_dashboard = _firma_dashboard(dashboard)
                    await websocket.send_json({"tipo": "dashboard", "datos": [dashboard]})
                else:
                    await websocket.send_json(
                        {
                            "tipo": "error",
                            "datos": [{"mensaje": "Tipo de mensaje no soportado."}],
                        }
                    )
            except asyncio.TimeoutError:
                db.expire_all()
                dashboard = _obtener_dashboard(
                    db=db,
                    id_empresa=id_empresa,
                    id_sucursal=id_sucursal_actual,
                )
                nueva_firma = _firma_dashboard(dashboard)
                if nueva_firma != firma_dashboard:
                    firma_dashboard = nueva_firma
                    await websocket.send_json({"tipo": "dashboard", "datos": [dashboard]})
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
