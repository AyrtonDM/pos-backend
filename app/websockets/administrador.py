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
from app.models.clientes import Cliente
from app.models.usuarios import Usuario, Persona

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


def _calcular_dashboard(id_empresa: int, id_sucursal: int | None = None) -> dict[str, Any]:
    db = SessionLocal()
    try:
        return _obtener_dashboard(
            db=db,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
    finally:
        db.close()


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

    ranking_clientes_rows = (
        db.query(
            Cliente.id_cliente,
            Persona.nombre_completo.label("nombre"),
            func.coalesce(func.sum(Venta.total), 0).label("total_comprado"),
            func.count(Venta.id_venta).label("cantidad_compras"),
            func.max(Venta.fecha).label("ultima_compra"),
        )
        .join(Venta, Cliente.id_cliente == Venta.id_cliente)
        .join(Usuario, Cliente.id_usuario == Usuario.id_usuario)
        .join(Persona, Usuario.id_persona == Persona.id_persona)
        .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
        .join(Caja, CajaSesion.id_caja == Caja.id_caja)
        .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
        .filter(Sucursal.id_empresa == id_empresa)
        .filter(Venta.fecha.between(inicio_30_dias, fin_hoy))
        .filter(Venta.estado != "ANULADA")
    )
    if id_sucursal is not None:
        ranking_clientes_rows = ranking_clientes_rows.filter(Sucursal.id_sucursal == id_sucursal)
        
    ranking_clientes_rows = ranking_clientes_rows.group_by(
        Cliente.id_cliente, Persona.nombre_completo
    ).all()

    ranking_clientes_final = []
    if ranking_clientes_rows:
        max_monto = max(float(row.total_comprado) for row in ranking_clientes_rows)
        max_frecuencia = max(int(row.cantidad_compras) for row in ranking_clientes_rows)
        now = datetime.utcnow()
        clientes_calculados = []
        
        for row in ranking_clientes_rows:
            total_comprado = float(row.total_comprado)
            cantidad_compras = int(row.cantidad_compras)
            
            monto_norm = (total_comprado / max_monto * 100) if max_monto > 0 else 0
            frec_norm = (cantidad_compras / max_frecuencia * 100) if max_frecuencia > 0 else 0
            
            dias_pasados = (now - row.ultima_compra).days if row.ultima_compra else 30
            recencia_norm = max(0, min(100, ((30 - dias_pasados) / 30) * 100))
            
            puntaje = (monto_norm * 0.50) + (frec_norm * 0.30) + (recencia_norm * 0.20)
            
            if puntaje >= 80:
                categoria = "Oro"
            elif puntaje >= 50:
                categoria = "Plata"
            else:
                categoria = "Bronce"
                
            ticket_promedio = round(total_comprado / cantidad_compras, 2) if cantidad_compras > 0 else 0
            
            clientes_calculados.append({
                "id_cliente": int(row.id_cliente),
                "nombre": row.nombre,
                "total_comprado": round(total_comprado, 2),
                "cantidad_compras": cantidad_compras,
                "ticket_promedio": float(ticket_promedio),
                "ultima_compra": row.ultima_compra.isoformat() if row.ultima_compra else None,
                "categoria": categoria,
                "puntaje": round(puntaje, 2)
            })
            
        clientes_calculados.sort(key=lambda x: x["puntaje"], reverse=True)
        
        for i, cliente in enumerate(clientes_calculados[:5]):
            cliente["posicion"] = i + 1
            ranking_clientes_final.append(cliente)

    recomendaciones_ia = []

    if productos_agotados > 0:
        recomendaciones_ia.append({
            "tipo": "inventario",
            "titulo": "Reponer productos agotados",
            "mensaje": f"Actualmente existen {productos_agotados} productos agotados.",
            "prioridad": "alta",
            "metrica": "productos_agotados",
            "valor": productos_agotados
        })

    if productos_bajo_stock > 0:
        total_productos = len(stocks)
        umbral_bajo_stock = 0.20
        prioridad_stock = "alta" if (total_productos > 0 and (productos_bajo_stock / total_productos) > umbral_bajo_stock) else "media"
        
        recomendaciones_ia.append({
            "tipo": "inventario",
            "titulo": "Revisar bajo stock",
            "mensaje": f"Existen {productos_bajo_stock} productos por debajo del stock mínimo de seguridad.",
            "prioridad": prioridad_stock,
            "metrica": "productos_bajo_stock",
            "valor": productos_bajo_stock
        })

    if ranking_clientes_final:
        mejor_cliente = ranking_clientes_final[0]
        if mejor_cliente["ultima_compra"]:
            dias_inactivo = (datetime.utcnow() - datetime.fromisoformat(mejor_cliente["ultima_compra"])).days
            if dias_inactivo >= 15:
                recomendaciones_ia.append({
                    "tipo": "oportunidad",
                    "titulo": "Cliente top inactivo",
                    "mensaje": f"El cliente top '{mejor_cliente['nombre']}' no compra desde hace {dias_inactivo} días. Considere una campaña de reactivación o beneficio personalizado.",
                    "prioridad": "media",
                    "metrica": "dias_inactivo",
                    "valor": dias_inactivo
                })

    if producto_estrella and (producto_estrella.unidades or 0) > 0:
        recomendaciones_ia.append({
            "tipo": "oportunidad",
            "titulo": "Impulsar producto estrella",
            "mensaje": f"Su producto más vendido hoy es '{producto_estrella.nombre}' con {int(producto_estrella.unidades)} unidades. Asegure su disponibilidad en vitrina.",
            "prioridad": "media",
            "metrica": "unidades_estrella",
            "valor": int(producto_estrella.unidades)
        })

    ventas_ultimos_7 = sum(item["total"] for item in evolucion if (hoy - timedelta(days=6)) <= datetime.fromisoformat(item["fecha"]).date() <= hoy)
    ventas_anteriores_7 = sum(item["total"] for item in evolucion if (hoy - timedelta(days=13)) <= datetime.fromisoformat(item["fecha"]).date() < (hoy - timedelta(days=6)))

    if ventas_anteriores_7 > 0:
        variacion = ((ventas_ultimos_7 - ventas_anteriores_7) / ventas_anteriores_7) * 100
        if variacion <= -15:
            recomendaciones_ia.append({
                "tipo": "alerta",
                "titulo": "Caída en ventas",
                "mensaje": f"Las ventas de los últimos 7 días han caído un {abs(round(variacion, 2))}% respecto a la semana anterior.",
                "prioridad": "media",
                "metrica": "variacion_ventas",
                "valor": round(variacion, 2)
            })
        elif variacion >= 20:
            recomendaciones_ia.append({
                "tipo": "oportunidad",
                "titulo": "Crecimiento en ventas",
                "mensaje": f"¡Excelente! Las ventas semanales crecieron un {round(variacion, 2)}% respecto a la semana anterior.",
                "prioridad": "baja",
                "metrica": "variacion_ventas",
                "valor": round(variacion, 2)
            })
    elif ventas_anteriores_7 == 0 and ventas_ultimos_7 > 0:
        recomendaciones_ia.append({
            "tipo": "oportunidad",
            "titulo": "Crecimiento en ventas",
            "mensaje": "Las ventas de esta semana han empezado a crecer respecto a los 7 días anteriores.",
            "prioridad": "baja",
            "metrica": "ventas_ultimos_7",
            "valor": round(ventas_ultimos_7, 2)
        })

    prioridad_peso = {"alta": 1, "media": 2, "baja": 3}
    recomendaciones_ia.sort(key=lambda x: prioridad_peso.get(x["prioridad"], 99))
    recomendaciones_ia = recomendaciones_ia[:5]

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
        "ranking_clientes": ranking_clientes_final,
        "recomendaciones_ia": recomendaciones_ia,
        "generado_en": datetime.utcnow().isoformat(),
    }


@router.websocket("/{id_empresa}")
async def administrador_dashboard(websocket: WebSocket, id_empresa: int):
    await websocket.accept()
    try:
        id_sucursal_actual: int | None = None
        dashboard = _calcular_dashboard(id_empresa=id_empresa)
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
                    dashboard = _calcular_dashboard(
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
                dashboard = _calcular_dashboard(
                    id_empresa=id_empresa,
                    id_sucursal=id_sucursal_actual,
                )
                nueva_firma = _firma_dashboard(dashboard)
                if nueva_firma != firma_dashboard:
                    firma_dashboard = nueva_firma
                    await websocket.send_json({"tipo": "dashboard", "datos": [dashboard]})
    except WebSocketDisconnect:
        pass
