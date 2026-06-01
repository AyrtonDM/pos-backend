from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
import unicodedata
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import obtener_clave_openai, obtener_modelo_reportes
from app.models.empresas import Caja, CajaSesion, Empresa, MovimientoCaja, Sucursal, TipoMovimientoCaja
from app.models.inventario import Stock
from app.models.inventario.movimiento_inventario import MovimientoInventario
from app.models.inventario.tipo_movimiento import TipoMovimiento
from app.models.productos import CategoriaProducto, Producto, SubcategoriaProducto
from app.models.ventas import DetalleVenta, MetodoPago, Venta, VentaPago
from app.models.clientes.cliente import Cliente
from app.models.usuarios.usuario import Usuario
from app.models.usuarios.persona import Persona
from app.schemas.reporte_schema import (
    ColumnaReporte,
    EspecificacionReporte,
    PlantillaReporte,
    RespuestaReporte,
    SolicitudReporte,
)


PLANTILLAS: list[dict[str, Any]] = [
    {
        "identificador": "movimientos_inventario",
        "nombre": "Movimientos de inventario",
        "descripcion": "Historial de movimientos de stock por producto, tipo, sucursal y usuario.",
        "metricas": ["cantidad"],
        "dimensiones": ["fecha", "producto", "tipo_movimiento", "sucursal", "usuario"],
        "formato": "tabla",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias"},
        "etiquetas": ["inventario", "movimientos", "historial", "kardex"],
    },
    {
        "identificador": "resumen_ventas",
        "nombre": "Resumen de ventas",
        "descripcion": "Resumen ejecutivo de ventas por periodo y sucursal.",
        "metricas": ["total_ventas", "cantidad_ventas", "ticket_promedio"],
        "dimensiones": ["fecha", "sucursal"],
        "formato": "tabla",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias", "granularidad_fecha": "dia"},
        "etiquetas": ["ventas", "resumen", "sucursal", "periodo"],
    },
    {
        "identificador": "ventas_por_sucursal",
        "nombre": "Ventas por sucursal",
        "descripcion": "Totales de ventas agrupados por sucursal.",
        "metricas": ["total_ventas", "cantidad_ventas"],
        "dimensiones": ["sucursal"],
        "formato": "barra",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias"},
        "etiquetas": ["ventas", "sucursal", "comparativo"],
    },
    {
        "identificador": "ventas_por_producto",
        "nombre": "Ventas por producto",
        "descripcion": "Ventas, cantidades y categoria de producto dentro de un periodo.",
        "metricas": ["total_ventas", "cantidad_vendida", "precio_promedio"],
        "dimensiones": ["producto", "categoria_producto"],
        "formato": "tabla",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias", "top_n": 10},
        "etiquetas": ["ventas", "producto", "categoria", "top"],
    },
    {
        "identificador": "productos_top",
        "nombre": "Productos mas vendidos",
        "descripcion": "Top N de productos por cantidad o por ventas.",
        "metricas": ["cantidad_vendida", "total_ventas"],
        "dimensiones": ["producto"],
        "formato": "tabla",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias", "top_n": 10},
        "etiquetas": ["top", "producto", "ventas", "cantidad"],
    },
    {
        "identificador": "alertas_stock",
        "nombre": "Alertas de stock",
        "descripcion": "Productos con stock igual o inferior al minimo.",
        "metricas": ["cantidad_actual", "stock_minimo", "diferencia"],
        "dimensiones": ["producto", "sucursal"],
        "formato": "tabla",
        "filtros_por_defecto": {"solo_bajo_minimo": True},
        "etiquetas": ["stock", "inventario", "alertas"],
    },
    {
        "identificador": "movimientos_caja",
        "nombre": "Movimientos de caja",
        "descripcion": "Entradas, salidas y neto de caja por periodo y sucursal.",
        "metricas": ["ingresos", "egresos", "neto"],
        "dimensiones": ["fecha", "sucursal", "tipo_movimiento"],
        "formato": "tabla",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias"},
        "etiquetas": ["caja", "movimientos", "saldo"],
    },
    {
        "identificador": "reparticion_metodos_pago",
        "nombre": "Reparticion por metodo de pago",
        "descripcion": "Distribucion de ventas por metodo de pago.",
        "metricas": ["total_ventas", "cantidad_transacciones"],
        "dimensiones": ["metodo_pago"],
        "formato": "torta",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias"},
        "etiquetas": ["pago", "ventas", "metodo"],
    },
    {
        "identificador": "comparar_periodos",
        "nombre": "Comparar periodos",
        "descripcion": "Comparacion entre un periodo actual y uno anterior.",
        "metricas": ["total_ventas", "cantidad_ventas", "crecimiento_pct"],
        "dimensiones": ["periodo"],
        "formato": "tarjetas",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias"},
        "etiquetas": ["comparativo", "periodo", "crecimiento"],
    },
    {
        "identificador": "ventas_detalle",
        "nombre": "Ventas (detalle)",
        "descripcion": "Listado de ventas (una fila por venta) con detalles basicos.",
        "metricas": [],
        "dimensiones": ["id_venta", "fecha", "sucursal", "cliente", "metodo_pago", "total"],
        "formato": "tabla",
        "filtros_por_defecto": {"periodo": "ultimos_30_dias"},
        "etiquetas": ["ventas", "detalle", "historial"],
    },
]


def _normalizar_texto(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor)
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter)).lower()


def _modelo_a_dict(modelo: Any) -> dict[str, Any]:
    if hasattr(modelo, "model_dump"):
        return modelo.model_dump()
    return modelo.dict()


def _decimal_a_numero(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {clave: _decimal_a_numero(subvalor) for clave, subvalor in valor.items()}
    if isinstance(valor, list):
        return [_decimal_a_numero(item) for item in valor]
    return valor


def _plantilla_por_identificador(identificador: str) -> dict[str, Any] | None:
    for plantilla in PLANTILLAS:
        if plantilla["identificador"] == identificador:
            return plantilla
    return None


def obtener_plantillas() -> list[PlantillaReporte]:
    return [PlantillaReporte(**plantilla) for plantilla in PLANTILLAS]


def obtener_plantilla(identificador: str) -> PlantillaReporte | None:
    plantilla = _plantilla_por_identificador(identificador)
    return PlantillaReporte(**plantilla) if plantilla else None


def _parsear_fecha(valor: Any, inicio_del_dia: bool) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime.combine(valor, time.min if inicio_del_dia else time.max)
    if isinstance(valor, str):
        texto = valor.strip()
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(texto)
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            return parsed
        except ValueError:
            try:
                parsed_date = date.fromisoformat(texto[:10])
                return datetime.combine(parsed_date, time.min if inicio_del_dia else time.max)
            except ValueError:
                pass

    hoy = datetime.utcnow()
    return datetime.combine(hoy.date(), time.min if inicio_del_dia else time.max)


def _plazo_predeterminado(filtros: dict[str, Any]) -> tuple[datetime, datetime]:
    hoy = datetime.utcnow()
    periodo = _normalizar_texto(str(filtros.get("periodo", "ultimos_30_dias")))

    if periodo in {"mes_actual", "month_to_date"}:
        inicio = datetime.combine(hoy.date().replace(day=1), time.min)
        fin = datetime.combine(hoy.date(), time.max)
        return inicio, fin

    if periodo in {"mes_anterior", "last_month"}:
        primer_dia_mes_actual = hoy.date().replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        inicio = datetime.combine(ultimo_dia_mes_anterior.replace(day=1), time.min)
        fin = datetime.combine(ultimo_dia_mes_anterior, time.max)
        return inicio, fin

    if "date_from" in filtros or "fecha_inicio" in filtros:
        inicio_raw = filtros.get("date_from") or filtros.get("fecha_inicio")
        fin_raw = filtros.get("date_to") or filtros.get("fecha_fin") or inicio_raw
        inicio = _parsear_fecha(inicio_raw, inicio_del_dia=True)
        fin = _parsear_fecha(fin_raw, inicio_del_dia=False)
        return inicio, fin

    dias = 30
    if periodo in {"ultimos_7_dias", "last_7_days"}:
        dias = 7
    elif periodo in {"ultimos_15_dias"}:
        dias = 15
    elif periodo in {"ultimos_90_dias"}:
        dias = 90

    inicio = datetime.combine((hoy - timedelta(days=dias)).date(), time.min)
    fin = datetime.combine(hoy.date(), time.max)
    return inicio, fin


def _clasificar_tipo_movimiento(nombre: str | None) -> str:
    if not nombre:
        return "desconocido"

    normalizado = _normalizar_texto(nombre)
    if any(palabra in normalizado for palabra in ["ingreso", "entrada", "abono", "cobro", "venta"]):
        return "ingreso"
    if any(palabra in normalizado for palabra in ["egreso", "salida", "retiro", "pago"]):
        return "egreso"
    return "desconocido"


def _responder_json_api(cuerpo: dict[str, Any]) -> dict[str, Any]:
    api_key = obtener_clave_openai()
    if not api_key:
        raise RuntimeError("No se encontro OPENAI_API_KEY en el entorno.")

    url = "https://api.openai.com/v1/chat/completions"
    datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
    solicitud = urllib.request.Request(
        url,
        data=datos,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
            contenido = respuesta.read().decode("utf-8")
            return json.loads(contenido)
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="ignore") if error.fp else ""
        raise RuntimeError(f"Error llamando a OpenAI: {error.code} {detalle}") from error


def _usar_openai() -> bool:
    valor = os.getenv("REPORTES_USAR_OPENAI", "true").strip().lower()
    return valor not in {"0", "false", "no", "off"}


def _inferir_especificacion_local(prompt: str) -> EspecificacionReporte:
    texto = _normalizar_texto(prompt)

    if any(palabra in texto for palabra in ["movimiento inventario", "movimientos en inventario", "movimientos de inventario", "historial de inventario", "kardex", "movimientos de stock"]):
        identificador = "movimientos_inventario"
    elif any(palabra in texto for palabra in ["stock", "inventario", "existencia"]):
        identificador = "alertas_stock"
    elif any(palabra in texto for palabra in ["detalle", "lista", "lista de ventas", "historial", "una fila por venta", "por venta", "detalle por venta"]):
        identificador = "ventas_detalle"
    elif any(palabra in texto for palabra in ["caja", "movimiento", "retiro", "ingreso"]):
        identificador = "movimientos_caja"
    elif any(palabra in texto for palabra in ["metodo de pago", "medio de pago", "pagos"]):
        identificador = "reparticion_metodos_pago"
    elif any(palabra in texto for palabra in ["comparar", "comparativo", "variacion", "crecimiento"]):
        identificador = "comparar_periodos"
    elif any(palabra in texto for palabra in ["producto", "productos"]):
        if any(palabra in texto for palabra in ["top", "mas vendidos", "lider"]):
            identificador = "productos_top"
        else:
            identificador = "ventas_por_producto"
    elif any(palabra in texto for palabra in ["sucursal", "sucursales"]):
        identificador = "ventas_por_sucursal"
    else:
        identificador = "resumen_ventas"

    plantilla = _plantilla_por_identificador(identificador)
    if not plantilla:
        raise RuntimeError("No se encontro una plantilla por defecto.")

    filtros = deepcopy(plantilla.get("filtros_por_defecto", {}))
    if "mes" in texto or "mensual" in texto:
        filtros["granularidad_fecha"] = "mes"
    if any(palabra in texto for palabra in ["dia", "diario", "dia a dia"]):
        filtros["granularidad_fecha"] = "dia"
    if any(palabra in texto for palabra in ["top 5", "top5"]):
        filtros["top_n"] = 5
    if any(palabra in texto for palabra in ["top 10", "top10"]):
        filtros["top_n"] = 10

    titulo = plantilla["nombre"]
    if "ultimo mes" in texto:
        titulo = f"{titulo} - ultimo mes"
        filtros["periodo"] = "mes_anterior"

    return EspecificacionReporte(
        identificador_plantilla=identificador,
        titulo=titulo,
        metricas=list(plantilla.get("metricas", [])),
        dimensiones=list(plantilla.get("dimensiones", [])),
        filtros=filtros,
        formato=plantilla.get("formato", "tabla"),
        solicita_aclaracion=False,
        confianza=0.55,
    )


class ReportesService:
    @staticmethod
    def obtener_catalogo() -> list[PlantillaReporte]:
        return obtener_plantillas()

    @staticmethod
    def interpretar_solicitud(solicitud: SolicitudReporte) -> tuple[EspecificacionReporte, list[str]]:
        plantilla_catalogo = obtener_plantillas()
        plantillas_json = [_modelo_a_dict(plantilla) for plantilla in plantilla_catalogo]

        instrucciones = (
            "Eres un asistente experto en reportes dinamicos para un POS. "
            "Debes responder solo con la llamada a la funcion JSON y escoger una plantilla existente. "
            "Siempre trabaja en espanol. Si el usuario es ambiguo, marca solicita_aclaracion=true y pregunta una sola pregunta corta. "
            "No inventes plantillas nuevas ni campos fuera del catalogo."
        )

        herramientas = [
            {
                "type": "function",
                "function": {
                    "name": "seleccionar_plantilla_reporte",
                    "description": "Selecciona la plantilla adecuada y devuelve la especificacion del reporte.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "identificador_plantilla": {"type": "string"},
                            "titulo": {"type": "string"},
                            "metricas": {"type": "array", "items": {"type": "string"}},
                            "dimensiones": {"type": "array", "items": {"type": "string"}},
                            "filtros": {"type": "object"},
                            "formato": {"type": "string"},
                            "solicita_aclaracion": {"type": "boolean"},
                            "pregunta": {"type": "string"},
                            "confianza": {"type": "number"},
                        },
                        "required": [
                            "identificador_plantilla",
                            "metricas",
                            "dimensiones",
                            "filtros",
                            "formato",
                            "solicita_aclaracion",
                        ],
                    },
                },
            }
        ]

        modelo = obtener_modelo_reportes()
        api_key = obtener_clave_openai()
        advertencias: list[str] = []

        if api_key and _usar_openai():
            cuerpo = {
                "model": modelo,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": instrucciones},
                    {
                        "role": "user",
                        "content": (
                            f"Solicitud del admin: {solicitud.prompt}\n\n"
                            f"Plantillas disponibles en JSON: {json.dumps(plantillas_json, ensure_ascii=False)}"
                        ),
                    },
                ],
                "tools": herramientas,
                "tool_choice": {"type": "function", "function": {"name": "seleccionar_plantilla_reporte"}},
            }

            try:
                respuesta = _responder_json_api(cuerpo)
                mensaje = respuesta["choices"][0]["message"]
                tool_calls = mensaje.get("tool_calls") or []
                if tool_calls:
                    argumentos = tool_calls[0]["function"]["arguments"]
                    datos = json.loads(argumentos)
                    especificacion = ReportesService._normalizar_especificacion(datos, plantilla_catalogo)
                    return especificacion, advertencias
            except Exception as exc:
                advertencias.append(f"Se uso interpretacion local por error con OpenAI: {exc}")

        especificacion = _inferir_especificacion_local(solicitud.prompt)
        return especificacion, advertencias

    @staticmethod
    def ejecutar_reporte(
        db: Session,
        solicitud: SolicitudReporte,
        empresa_id: int,
        especificacion: EspecificacionReporte | None = None,
    ) -> RespuestaReporte:
        advertencias: list[str] = []
        if especificacion is None:
            especificacion, advertencias = ReportesService.interpretar_solicitud(solicitud)

        empresa = db.query(Empresa).filter(Empresa.id_empresa == empresa_id).first()
        if not empresa:
            raise ValueError("La empresa solicitada no existe.")

        plantilla = _plantilla_por_identificador(especificacion.identificador_plantilla)
        if not plantilla:
            raise ValueError("La plantilla solicitada no existe.")

        columnas, filas, agregados, grafico, advertencias_ejecucion = ReportesService._ejecutar_por_plantilla(
            db=db,
            especificacion=especificacion,
            plantilla=plantilla,
            empresa_id=empresa_id,
        )

        return RespuestaReporte(
            id_reporte=f"rep_{uuid.uuid4().hex[:12]}",
            titulo=especificacion.titulo,
            identificador_plantilla=especificacion.identificador_plantilla,
            especificacion=especificacion,
            columnas=columnas,
            filas=filas,
            agregados=agregados,
            grafico=grafico,
            advertencias=advertencias + advertencias_ejecucion,
            fecha_generacion=datetime.utcnow().date(),
        )

    @staticmethod
    def _normalizar_especificacion(
        datos: dict[str, Any],
        catalogo: list[PlantillaReporte],
    ) -> EspecificacionReporte:
        identificador = str(datos.get("identificador_plantilla", "")).strip()
        plantilla = next((item for item in catalogo if item.identificador == identificador), None)
        if not plantilla:
            raise ValueError("La plantilla sugerida no existe en el catalogo.")

        metrica_permitidas = set(plantilla.metricas)
        dimensiones_permitidas = set(plantilla.dimensiones)

        metricas = [metrica for metrica in datos.get("metricas", []) if metrica in metrica_permitidas]
        dimensiones = [dimension for dimension in datos.get("dimensiones", []) if dimension in dimensiones_permitidas]

        filtros = datos.get("filtros") or {}
        formato = str(datos.get("formato") or plantilla.formato or "tabla")
        solicita_aclaracion = bool(datos.get("solicita_aclaracion", False))
        pregunta = datos.get("pregunta")
        confianza = datos.get("confianza")

        return EspecificacionReporte(
            identificador_plantilla=identificador,
            titulo=str(datos.get("titulo") or plantilla.nombre),
            metricas=metricas or list(plantilla.metricas),
            dimensiones=dimensiones or list(plantilla.dimensiones),
            filtros=filtros,
            formato=formato,
            solicita_aclaracion=solicita_aclaracion,
            pregunta=pregunta,
            confianza=confianza,
        )

    @staticmethod
    def _ejecutar_por_plantilla(
        db: Session,
        especificacion: EspecificacionReporte,
        plantilla: dict[str, Any],
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        ejecutor = {
                "resumen_ventas": ReportesService._reporte_resumen_ventas,
                "movimientos_inventario": ReportesService._reporte_movimientos_inventario,
            "ventas_por_sucursal": ReportesService._reporte_ventas_por_sucursal,
            "ventas_por_producto": ReportesService._reporte_ventas_por_producto,
            "productos_top": ReportesService._reporte_productos_top,
            "alertas_stock": ReportesService._reporte_alertas_stock,
            "movimientos_caja": ReportesService._reporte_movimientos_caja,
            "reparticion_metodos_pago": ReportesService._reporte_metodos_pago,
            "comparar_periodos": ReportesService._reporte_comparar_periodos,
                "ventas_detalle": ReportesService._reporte_ventas_detalle,
        }.get(especificacion.identificador_plantilla)

        if not ejecutor:
            raise ValueError("No existe un ejecutor para la plantilla solicitada.")

        return ejecutor(db=db, especificacion=especificacion, empresa_id=empresa_id)

    @staticmethod
    def _reporte_resumen_ventas(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)
        granularidad = _normalizar_texto(str(especificacion.filtros.get("granularidad_fecha", "dia")))
        trunc = "month" if granularidad == "mes" else "day"

        fecha_grupo = func.date_trunc(trunc, Venta.fecha).label("fecha")
        sucursal_nombre = Sucursal.nombre.label("sucursal")

        consulta = (
            db.query(
                fecha_grupo,
                sucursal_nombre,
                func.count(Venta.id_venta).label("cantidad_ventas"),
                func.coalesce(func.sum(Venta.total), 0).label("total_ventas"),
                func.coalesce(func.avg(Venta.total), 0).label("ticket_promedio"),
            )
            .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
            .join(Caja, CajaSesion.id_caja == Caja.id_caja)
            .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
            .filter(Sucursal.id_empresa == empresa_id)
            .filter(Venta.fecha.between(inicio, fin))
            .group_by(fecha_grupo, sucursal_nombre)
            .order_by(fecha_grupo.asc(), sucursal_nombre.asc())
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "fecha": fila.fecha.isoformat() if fila.fecha else None,
                    "sucursal": fila.sucursal,
                    "cantidad_ventas": int(fila.cantidad_ventas or 0),
                    "total_ventas": float(fila.total_ventas or 0),
                    "ticket_promedio": float(fila.ticket_promedio or 0),
                }
            )

        agregados = {
            "cantidad_ventas": int(sum(fila["cantidad_ventas"] for fila in filas)),
            "total_ventas": float(sum(fila["total_ventas"] for fila in filas)),
        }
        agregados["ticket_promedio"] = round(
            agregados["total_ventas"] / agregados["cantidad_ventas"],
            2,
        ) if agregados["cantidad_ventas"] else 0.0

        columnas = [
            ColumnaReporte(nombre="fecha", etiqueta="Fecha", tipo="fecha"),
            ColumnaReporte(nombre="sucursal", etiqueta="Sucursal", tipo="texto"),
            ColumnaReporte(nombre="cantidad_ventas", etiqueta="Cantidad de ventas", tipo="entero"),
            ColumnaReporte(nombre="total_ventas", etiqueta="Total ventas", tipo="moneda"),
            ColumnaReporte(nombre="ticket_promedio", etiqueta="Ticket promedio", tipo="moneda"),
        ]
        return columnas, filas, agregados, None, []

    @staticmethod
    def _reporte_ventas_por_sucursal(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)
        consulta = (
            db.query(
                Sucursal.nombre.label("sucursal"),
                func.count(Venta.id_venta).label("cantidad_ventas"),
                func.coalesce(func.sum(Venta.total), 0).label("total_ventas"),
                func.coalesce(func.avg(Venta.total), 0).label("ticket_promedio"),
            )
            .select_from(Sucursal)
            .outerjoin(Caja, Sucursal.id_sucursal == Caja.id_sucursal)
            .outerjoin(CajaSesion, Caja.id_caja == CajaSesion.id_caja)
            .outerjoin(
                Venta,
                and_(
                    Venta.id_caja_sesion == CajaSesion.id_caja_sesion,
                    Venta.fecha.between(inicio, fin),
                ),
            )
            .filter(Sucursal.id_empresa == empresa_id)
            .group_by(Sucursal.id_sucursal, Sucursal.nombre)
            .order_by(func.coalesce(func.sum(Venta.total), 0).desc(), Sucursal.nombre.asc())
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "sucursal": fila.sucursal,
                    "cantidad_ventas": int(fila.cantidad_ventas or 0),
                    "total_ventas": float(fila.total_ventas or 0),
                    "ticket_promedio": float(fila.ticket_promedio or 0),
                }
            )

        agregados = {
            "cantidad_ventas": int(sum(fila["cantidad_ventas"] for fila in filas)),
            "total_ventas": float(sum(fila["total_ventas"] for fila in filas)),
        }
        agregados["ticket_promedio"] = round(
            agregados["total_ventas"] / agregados["cantidad_ventas"],
            2,
        ) if agregados["cantidad_ventas"] else 0.0

        columnas = [
            ColumnaReporte(nombre="sucursal", etiqueta="Sucursal", tipo="texto"),
            ColumnaReporte(nombre="cantidad_ventas", etiqueta="Cantidad de ventas", tipo="entero"),
            ColumnaReporte(nombre="total_ventas", etiqueta="Total ventas", tipo="moneda"),
            ColumnaReporte(nombre="ticket_promedio", etiqueta="Ticket promedio", tipo="moneda"),
        ]
        grafico = {
            "tipo": "barra",
            "etiqueta_eje_x": "Sucursal",
            "etiqueta_eje_y": "Total ventas",
            "series": [
                {"nombre": "Total ventas", "datos": [fila["total_ventas"] for fila in filas]},
            ],
            "categorias": [fila["sucursal"] for fila in filas],
        }
        return columnas, filas, agregados, grafico, []

    @staticmethod
    def _reporte_ventas_por_producto(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)
        top_n = int(especificacion.filtros.get("top_n", 10))

        consulta = (
            db.query(
                Producto.nombre.label("producto"),
                CategoriaProducto.nombre.label("categoria_producto"),
                func.sum(DetalleVenta.cantidad).label("cantidad_vendida"),
                func.coalesce(func.sum(DetalleVenta.total), 0).label("total_ventas"),
                func.coalesce(func.avg(DetalleVenta.precio_unitario), 0).label("precio_promedio"),
            )
            .join(Venta, DetalleVenta.id_venta == Venta.id_venta)
            .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
            .join(Caja, CajaSesion.id_caja == Caja.id_caja)
            .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
            .join(Producto, DetalleVenta.id_producto == Producto.id_producto)
            .outerjoin(SubcategoriaProducto, Producto.id_subcategoria == SubcategoriaProducto.id_subcategoria)
            .outerjoin(CategoriaProducto, SubcategoriaProducto.id_categoria_producto == CategoriaProducto.id_categoria_producto)
            .filter(Sucursal.id_empresa == empresa_id)
            .filter(Venta.fecha.between(inicio, fin))
            .group_by(Producto.nombre, CategoriaProducto.nombre)
            .order_by(func.sum(DetalleVenta.total).desc())
            .limit(top_n)
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "producto": fila.producto,
                    "categoria_producto": fila.categoria_producto,
                    "cantidad_vendida": int(fila.cantidad_vendida or 0),
                    "total_ventas": float(fila.total_ventas or 0),
                    "precio_promedio": float(fila.precio_promedio or 0),
                }
            )

        agregados = {
            "cantidad_vendida": int(sum(fila["cantidad_vendida"] for fila in filas)),
            "total_ventas": float(sum(fila["total_ventas"] for fila in filas)),
        }

        columnas = [
            ColumnaReporte(nombre="producto", etiqueta="Producto", tipo="texto"),
            ColumnaReporte(nombre="categoria_producto", etiqueta="Categoria", tipo="texto"),
            ColumnaReporte(nombre="cantidad_vendida", etiqueta="Cantidad vendida", tipo="entero"),
            ColumnaReporte(nombre="total_ventas", etiqueta="Total ventas", tipo="moneda"),
            ColumnaReporte(nombre="precio_promedio", etiqueta="Precio promedio", tipo="moneda"),
        ]
        grafico = {
            "tipo": "barra",
            "etiqueta_eje_x": "Producto",
            "etiqueta_eje_y": "Total ventas",
            "series": [
                {"nombre": "Total ventas", "datos": [fila["total_ventas"] for fila in filas]},
            ],
            "categorias": [fila["producto"] for fila in filas],
        }
        return columnas, filas, agregados, grafico, []

    @staticmethod
    def _reporte_productos_top(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)
        top_n = int(especificacion.filtros.get("top_n", 10))

        consulta = (
            db.query(
                Producto.nombre.label("producto"),
                func.sum(DetalleVenta.cantidad).label("cantidad_vendida"),
                func.coalesce(func.sum(DetalleVenta.total), 0).label("total_ventas"),
            )
            .join(Venta, DetalleVenta.id_venta == Venta.id_venta)
            .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
            .join(Caja, CajaSesion.id_caja == Caja.id_caja)
            .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
            .join(Producto, DetalleVenta.id_producto == Producto.id_producto)
            .filter(Sucursal.id_empresa == empresa_id)
            .filter(Venta.fecha.between(inicio, fin))
            .group_by(Producto.nombre)
            .order_by(func.sum(DetalleVenta.cantidad).desc())
            .limit(top_n)
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "producto": fila.producto,
                    "cantidad_vendida": int(fila.cantidad_vendida or 0),
                    "total_ventas": float(fila.total_ventas or 0),
                }
            )

        agregados = {
            "cantidad_vendida": int(sum(fila["cantidad_vendida"] for fila in filas)),
            "total_ventas": float(sum(fila["total_ventas"] for fila in filas)),
        }

        columnas = [
            ColumnaReporte(nombre="producto", etiqueta="Producto", tipo="texto"),
            ColumnaReporte(nombre="cantidad_vendida", etiqueta="Cantidad vendida", tipo="entero"),
            ColumnaReporte(nombre="total_ventas", etiqueta="Total ventas", tipo="moneda"),
        ]
        grafico = {
            "tipo": "barra",
            "etiqueta_eje_x": "Producto",
            "etiqueta_eje_y": "Cantidad vendida",
            "series": [
                {"nombre": "Cantidad vendida", "datos": [fila["cantidad_vendida"] for fila in filas]},
            ],
            "categorias": [fila["producto"] for fila in filas],
        }
        return columnas, filas, agregados, grafico, []

    @staticmethod
    def _reporte_alertas_stock(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        solo_bajo_minimo = bool(especificacion.filtros.get("solo_bajo_minimo", True))
        consulta = (
            db.query(
                Producto.nombre.label("producto"),
                Sucursal.nombre.label("sucursal"),
                Stock.cantidad.label("cantidad_actual"),
                Stock.stock_minimo.label("stock_minimo"),
            )
            .join(Producto, Stock.id_producto == Producto.id_producto)
            .join(Sucursal, Stock.id_sucursal == Sucursal.id_sucursal)
            .filter(Sucursal.id_empresa == empresa_id)
            .order_by(Sucursal.nombre.asc(), Producto.nombre.asc())
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            cantidad = int(fila.cantidad_actual or 0)
            minimo = int(fila.stock_minimo or 0)
            if solo_bajo_minimo and cantidad > minimo:
                continue
            filas.append(
                {
                    "producto": fila.producto,
                    "sucursal": fila.sucursal,
                    "cantidad_actual": cantidad,
                    "stock_minimo": minimo,
                    "diferencia": cantidad - minimo,
                }
            )

        agregados = {
            "alertas": len(filas),
            "cantidad_actual_total": int(sum(fila["cantidad_actual"] for fila in filas)),
        }

        columnas = [
            ColumnaReporte(nombre="producto", etiqueta="Producto", tipo="texto"),
            ColumnaReporte(nombre="sucursal", etiqueta="Sucursal", tipo="texto"),
            ColumnaReporte(nombre="cantidad_actual", etiqueta="Cantidad actual", tipo="entero"),
            ColumnaReporte(nombre="stock_minimo", etiqueta="Stock minimo", tipo="entero"),
            ColumnaReporte(nombre="diferencia", etiqueta="Diferencia", tipo="entero"),
        ]
        return columnas, filas, agregados, None, []

    @staticmethod
    def _reporte_movimientos_inventario(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)

        consulta = (
            db.query(
                MovimientoInventario.id_movimiento_inventario.label("id_movimiento_inventario"),
                MovimientoInventario.fecha_movimiento.label("fecha_movimiento"),
                Producto.nombre.label("producto"),
                TipoMovimiento.nombre.label("tipo_movimiento"),
                TipoMovimiento.direccion.label("direccion"),
                MovimientoInventario.cantidad.label("cantidad"),
                Sucursal.nombre.label("sucursal"),
                Persona.nombre_completo.label("usuario"),
                MovimientoInventario.observacion.label("observacion"),
            )
            .join(Producto, MovimientoInventario.id_producto == Producto.id_producto)
            .join(TipoMovimiento, MovimientoInventario.id_tipo_movimiento == TipoMovimiento.id_tipo_movimiento)
            .join(Usuario, MovimientoInventario.id_usuario == Usuario.id_usuario)
            .join(Persona, Usuario.id_persona == Persona.id_persona)
            .outerjoin(Sucursal, MovimientoInventario.id_sucursal == Sucursal.id_sucursal)
            .filter(
                (Sucursal.id_empresa == empresa_id) | (MovimientoInventario.id_sucursal.is_(None))
            )
            .filter(MovimientoInventario.fecha_movimiento.between(inicio, fin))
            .order_by(MovimientoInventario.fecha_movimiento.asc())
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "id_movimiento_inventario": int(fila.id_movimiento_inventario),
                    "fecha_movimiento": fila.fecha_movimiento.isoformat() if fila.fecha_movimiento else None,
                    "producto": fila.producto,
                    "tipo_movimiento": fila.tipo_movimiento,
                    "direccion": fila.direccion,
                    "cantidad": int(fila.cantidad or 0),
                    "sucursal": fila.sucursal,
                    "usuario": fila.usuario,
                    "observacion": fila.observacion,
                }
            )

        agregados = {
            "cantidad_movimientos": len(filas),
            "cantidad_total": int(sum(fila["cantidad"] for fila in filas)),
        }

        columnas = [
            ColumnaReporte(nombre="id_movimiento_inventario", etiqueta="ID Movimiento", tipo="entero"),
            ColumnaReporte(nombre="fecha_movimiento", etiqueta="Fecha", tipo="fecha"),
            ColumnaReporte(nombre="producto", etiqueta="Producto", tipo="texto"),
            ColumnaReporte(nombre="tipo_movimiento", etiqueta="Tipo movimiento", tipo="texto"),
            ColumnaReporte(nombre="direccion", etiqueta="Direccion", tipo="texto"),
            ColumnaReporte(nombre="cantidad", etiqueta="Cantidad", tipo="entero"),
            ColumnaReporte(nombre="sucursal", etiqueta="Sucursal", tipo="texto"),
            ColumnaReporte(nombre="usuario", etiqueta="Usuario", tipo="texto"),
            ColumnaReporte(nombre="observacion", etiqueta="Observacion", tipo="texto"),
        ]

        return columnas, filas, agregados, None, []

    @staticmethod
    def _reporte_movimientos_caja(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)
        fecha_grupo = func.date_trunc("day", MovimientoCaja.fecha).label("fecha")
        consulta = (
            db.query(
                fecha_grupo,
                Sucursal.nombre.label("sucursal"),
                TipoMovimientoCaja.nombre.label("tipo_movimiento"),
                func.coalesce(func.sum(MovimientoCaja.monto), 0).label("monto"),
            )
            .join(CajaSesion, MovimientoCaja.id_caja_sesion == CajaSesion.id_caja_sesion)
            .join(Caja, CajaSesion.id_caja == Caja.id_caja)
            .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
            .join(TipoMovimientoCaja, MovimientoCaja.id_tipo_movimiento_caja == TipoMovimientoCaja.id_tipo_movimiento_caja)
            .filter(Sucursal.id_empresa == empresa_id)
            .filter(MovimientoCaja.fecha.between(inicio, fin))
            .group_by(fecha_grupo, Sucursal.nombre, TipoMovimientoCaja.nombre)
            .order_by(fecha_grupo.asc())
        )

        filas: list[dict[str, Any]] = []
        ingresos = Decimal("0")
        egresos = Decimal("0")
        advertencias: list[str] = []

        for fila in consulta.all():
            clasificacion = _clasificar_tipo_movimiento(fila.tipo_movimiento)
            monto = Decimal(str(fila.monto or 0))
            if clasificacion == "ingreso":
                ingresos += monto
            elif clasificacion == "egreso":
                egresos += monto
            else:
                advertencias.append(
                    f"No se pudo clasificar el movimiento de caja '{fila.tipo_movimiento}' como ingreso o egreso."
                )

            filas.append(
                {
                    "fecha": fila.fecha.isoformat() if fila.fecha else None,
                    "sucursal": fila.sucursal,
                    "tipo_movimiento": fila.tipo_movimiento,
                    "monto": float(monto),
                    "clasificacion": clasificacion,
                }
            )

        agregados = {
            "ingresos": float(ingresos),
            "egresos": float(egresos),
            "neto": float(ingresos - egresos),
        }

        columnas = [
            ColumnaReporte(nombre="fecha", etiqueta="Fecha", tipo="fecha"),
            ColumnaReporte(nombre="sucursal", etiqueta="Sucursal", tipo="texto"),
            ColumnaReporte(nombre="tipo_movimiento", etiqueta="Tipo movimiento", tipo="texto"),
            ColumnaReporte(nombre="monto", etiqueta="Monto", tipo="moneda"),
            ColumnaReporte(nombre="clasificacion", etiqueta="Clasificacion", tipo="texto"),
        ]
        return columnas, filas, agregados, None, advertencias

    @staticmethod
    def _reporte_metodos_pago(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)
        consulta = (
            db.query(
                MetodoPago.nombre.label("metodo_pago"),
                func.count(VentaPago.id_venta).label("cantidad_transacciones"),
                func.coalesce(func.sum(VentaPago.monto), 0).label("total_ventas"),
            )
            .join(MetodoPago, VentaPago.id_metodo_pago == MetodoPago.id_metodo_pago)
            .join(Venta, VentaPago.id_venta == Venta.id_venta)
            .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
            .join(Caja, CajaSesion.id_caja == Caja.id_caja)
            .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
            .filter(Sucursal.id_empresa == empresa_id)
            .filter(Venta.fecha.between(inicio, fin))
            .group_by(MetodoPago.nombre)
            .order_by(func.sum(VentaPago.monto).desc())
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "metodo_pago": fila.metodo_pago,
                    "cantidad_transacciones": int(fila.cantidad_transacciones or 0),
                    "total_ventas": float(fila.total_ventas or 0),
                }
            )

        agregados = {
            "cantidad_transacciones": int(sum(fila["cantidad_transacciones"] for fila in filas)),
            "total_ventas": float(sum(fila["total_ventas"] for fila in filas)),
        }

        columnas = [
            ColumnaReporte(nombre="metodo_pago", etiqueta="Metodo de pago", tipo="texto"),
            ColumnaReporte(nombre="cantidad_transacciones", etiqueta="Cantidad transacciones", tipo="entero"),
            ColumnaReporte(nombre="total_ventas", etiqueta="Total ventas", tipo="moneda"),
        ]
        grafico = {
            "tipo": "torta",
            "etiqueta_eje_x": "Metodo de pago",
            "etiqueta_eje_y": "Total ventas",
            "series": [
                {"nombre": "Total ventas", "datos": [fila["total_ventas"] for fila in filas]},
            ],
            "categorias": [fila["metodo_pago"] for fila in filas],
        }
        return columnas, filas, agregados, grafico, []

    @staticmethod
    def _reporte_comparar_periodos(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio_actual, fin_actual = _plazo_predeterminado(especificacion.filtros)
        duracion = fin_actual - inicio_actual
        inicio_anterior = inicio_actual - duracion - timedelta(seconds=1)
        fin_anterior = inicio_actual - timedelta(seconds=1)

        def _totales(inicio: datetime, fin: datetime) -> dict[str, Any]:
            total_ventas, cantidad_ventas = (
                db.query(
                    func.coalesce(func.sum(Venta.total), 0),
                    func.count(Venta.id_venta),
                )
                .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
                .join(Caja, CajaSesion.id_caja == Caja.id_caja)
                .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
                .filter(Sucursal.id_empresa == empresa_id)
                .filter(Venta.fecha.between(inicio, fin))
                .one()
            )
            return {
                "total_ventas": float(total_ventas or 0),
                "cantidad_ventas": int(cantidad_ventas or 0),
            }

        actual = _totales(inicio_actual, fin_actual)
        anterior = _totales(inicio_anterior, fin_anterior)

        crecimiento = 0.0
        if anterior["total_ventas"]:
            crecimiento = round(((actual["total_ventas"] - anterior["total_ventas"]) / anterior["total_ventas"]) * 100, 2)

        filas = [
            {"periodo": "actual", **actual},
            {"periodo": "anterior", **anterior},
        ]
        agregados = {
            "total_ventas_actual": actual["total_ventas"],
            "total_ventas_anterior": anterior["total_ventas"],
            "crecimiento_pct": crecimiento,
        }
        columnas = [
            ColumnaReporte(nombre="periodo", etiqueta="Periodo", tipo="texto"),
            ColumnaReporte(nombre="total_ventas", etiqueta="Total ventas", tipo="moneda"),
            ColumnaReporte(nombre="cantidad_ventas", etiqueta="Cantidad ventas", tipo="entero"),
        ]
        grafico = {
            "tipo": "comparativo",
            "categorias": ["actual", "anterior"],
            "series": [
                {"nombre": "Total ventas", "datos": [actual["total_ventas"], anterior["total_ventas"]]},
            ],
        }
        return columnas, filas, agregados, grafico, []

    @staticmethod
    def _reporte_ventas_detalle(
        db: Session,
        especificacion: EspecificacionReporte,
        empresa_id: int,
    ) -> tuple[list[ColumnaReporte], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
        inicio, fin = _plazo_predeterminado(especificacion.filtros)

        consulta = (
            db.query(
                Venta.id_venta.label("id_venta"),
                Venta.fecha.label("fecha"),
                Sucursal.nombre.label("sucursal"),
                Persona.nombre_completo.label("cliente"),
                MetodoPago.nombre.label("metodo_pago"),
                func.coalesce(Venta.total, 0).label("total"),
            )
            .join(CajaSesion, Venta.id_caja_sesion == CajaSesion.id_caja_sesion)
            .join(Caja, CajaSesion.id_caja == Caja.id_caja)
            .join(Sucursal, Caja.id_sucursal == Sucursal.id_sucursal)
            .outerjoin(Cliente, Venta.id_cliente == Cliente.id_cliente)
            .outerjoin(Usuario, Cliente.id_usuario == Usuario.id_usuario)
            .outerjoin(Persona, Usuario.id_persona == Persona.id_persona)
            .outerjoin(VentaPago, Venta.id_venta == VentaPago.id_venta)
            .outerjoin(MetodoPago, VentaPago.id_metodo_pago == MetodoPago.id_metodo_pago)
            .filter(Sucursal.id_empresa == empresa_id)
            .filter(Venta.fecha.between(inicio, fin))
            .order_by(Venta.fecha.asc())
        )

        filas: list[dict[str, Any]] = []
        for fila in consulta.all():
            filas.append(
                {
                    "id_venta": int(fila.id_venta),
                    "fecha": fila.fecha.isoformat() if fila.fecha else None,
                    "sucursal": fila.sucursal,
                    "cliente": fila.cliente if fila.cliente else None,
                    "metodo_pago": fila.metodo_pago if fila.metodo_pago else None,
                    "total": float(fila.total or 0),
                }
            )

        agregados = {
            "cantidad_ventas": len(filas),
            "total_ventas": float(sum(fila["total"] for fila in filas)),
        }

        columnas = [
            ColumnaReporte(nombre="id_venta", etiqueta="ID Venta", tipo="entero"),
            ColumnaReporte(nombre="fecha", etiqueta="Fecha", tipo="fecha"),
            ColumnaReporte(nombre="sucursal", etiqueta="Sucursal", tipo="texto"),
            ColumnaReporte(nombre="cliente", etiqueta="Cliente", tipo="texto"),
            ColumnaReporte(nombre="metodo_pago", etiqueta="Metodo de pago", tipo="texto"),
            ColumnaReporte(nombre="total", etiqueta="Total", tipo="moneda"),
        ]

        return columnas, filas, agregados, None, []