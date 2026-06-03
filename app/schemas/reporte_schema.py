from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class PlantillaReporte(BaseModel):
    identificador: str
    nombre: str
    descripcion: str
    metricas: list[str] = Field(default_factory=list)
    dimensiones: list[str] = Field(default_factory=list)
    formato: str = "tabla"
    filtros_por_defecto: dict[str, Any] = Field(default_factory=dict)
    etiquetas: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SolicitudReporte(BaseModel):
    prompt: str


class EspecificacionReporte(BaseModel):
    identificador_plantilla: str
    titulo: str
    metricas: list[str] = Field(default_factory=list)
    dimensiones: list[str] = Field(default_factory=list)
    filtros: dict[str, Any] = Field(default_factory=dict)
    formato: str = "tabla"
    solicita_aclaracion: bool = False
    pregunta: str | None = None
    confianza: float | None = None

    class Config:
        from_attributes = True


class ColumnaReporte(BaseModel):
    nombre: str
    etiqueta: str
    tipo: str = "texto"


class RespuestaReporte(BaseModel):
    id_reporte: str
    titulo: str
    identificador_plantilla: str
    estado: str = "listo"
    especificacion: EspecificacionReporte | None = None
    columnas: list[ColumnaReporte] = Field(default_factory=list)
    filas: list[dict[str, Any]] = Field(default_factory=list)
    agregados: dict[str, Any] = Field(default_factory=dict)
    grafico: dict[str, Any] | None = None
    advertencias: list[str] = Field(default_factory=list)
    fecha_generacion: date | None = None


class RespuestaInterpretacion(BaseModel):
    especificacion: EspecificacionReporte
    plantilla: PlantillaReporte | None = None
    advertencias: list[str] = Field(default_factory=list)


class ProductoVendidoResumen(BaseModel):
    posicion: int
    id_producto: int
    producto: str
    unidades: int


class VentasDiaResumen(BaseModel):
    total_ventas: int
    monto_vendido: float
    ticket_promedio: float
    productos_vendidos: int


class SucursalResumenVentas(BaseModel):
    id_sucursal: int
    sucursal: str
    ventas_dia: VentasDiaResumen
    top_productos: list[ProductoVendidoResumen] = Field(default_factory=list)


class TotalEmpresaResumenVentas(BaseModel):
    total_ventas: int
    monto_vendido: float
    ticket_promedio: float
    productos_vendidos: int


class ResumenVentasEmpresaResponse(BaseModel):
    id_empresa: int
    fecha: date
    sucursales: list[SucursalResumenVentas]
    total_empresa: TotalEmpresaResumenVentas


class VentaDetalleReporte(BaseModel):
    id_venta: int
    numero_venta: str
    hora: str
    cliente: str | None
    subtotal: float
    descuento: float
    total: float


class ResumenSucursalDetalleVentas(BaseModel):
    total_registros: int
    total_vendido: float


class SucursalDetalleVentas(BaseModel):
    id_sucursal: int
    sucursal: str
    ventas: list[VentaDetalleReporte] = Field(default_factory=list)
    resumen_sucursal: ResumenSucursalDetalleVentas


class TotalEmpresaDetalleVentas(BaseModel):
    total_registros: int
    total_vendido: float


class DetalleVentasEmpresaResponse(BaseModel):
    id_empresa: int
    fecha: date
    sucursales: list[SucursalDetalleVentas]
    total_empresa: TotalEmpresaDetalleVentas


class ProductoEstadoInventario(BaseModel):
    id_producto: int
    producto: str
    stock_actual: int
    stock_minimo: int | None
    stock_maximo: int | None
    estado: str


class ResumenSucursalEstadoInventario(BaseModel):
    total_productos: int
    productos_bajo_stock: int
    productos_sobre_stock: int
    productos_agotados: int


class SucursalEstadoInventario(BaseModel):
    id_sucursal: int
    sucursal: str
    productos: list[ProductoEstadoInventario] = Field(default_factory=list)
    resumen_sucursal: ResumenSucursalEstadoInventario


class TotalEmpresaEstadoInventario(BaseModel):
    total_productos: int
    productos_bajo_stock: int
    productos_sobre_stock: int
    productos_agotados: int


class EstadoInventarioEmpresaResponse(BaseModel):
    id_empresa: int
    fecha: date
    sucursales: list[SucursalEstadoInventario]
    total_empresa: TotalEmpresaEstadoInventario


class MovimientoInventarioReporte(BaseModel):
    id_movimiento_inventario: int
    fecha: date
    tipo_movimiento: str
    direccion: str
    producto: str
    cantidad: int


class ResumenSucursalMovimientosInventario(BaseModel):
    total_entradas: int
    total_salidas: int


class SucursalMovimientosInventario(BaseModel):
    id_sucursal: int
    sucursal: str
    movimientos: list[MovimientoInventarioReporte] = Field(default_factory=list)
    resumen_sucursal: ResumenSucursalMovimientosInventario


class TotalEmpresaMovimientosInventario(BaseModel):
    total_entradas: int
    total_salidas: int


class MovimientosInventarioEmpresaResponse(BaseModel):
    id_empresa: int
    fecha_inicio: date
    fecha_fin: date
    sucursales: list[SucursalMovimientosInventario]
    total_empresa: TotalEmpresaMovimientosInventario


class CajaResumenReporte(BaseModel):
    id_caja: int
    id_caja_sesion: int
    caja: str
    estado: str
    apertura: str
    cierre: str | None


class ResumenSucursalCajas(BaseModel):
    total_cajas: int
    cajas_abiertas: int
    cajas_cerradas: int
    ingresos: float
    egresos: float
    flujo_neto: float


class SucursalResumenCajas(BaseModel):
    id_sucursal: int
    sucursal: str
    cajas: list[CajaResumenReporte] = Field(default_factory=list)
    resumen_sucursal: ResumenSucursalCajas


class TotalEmpresaResumenCajas(BaseModel):
    total_cajas: int
    cajas_abiertas: int
    cajas_cerradas: int
    ingresos: float
    egresos: float
    flujo_neto: float


class ResumenCajasEmpresaResponse(BaseModel):
    id_empresa: int
    fecha: date
    sucursales: list[SucursalResumenCajas]
    total_empresa: TotalEmpresaResumenCajas


class MovimientoCajaReporte(BaseModel):
    id_movimiento_caja: int
    hora: str
    caja: str
    tipo: str
    concepto: str | None
    monto: float


class ResumenSucursalMovimientosCaja(BaseModel):
    total_movimientos: int
    total_ingresos: float
    total_egresos: float


class SucursalMovimientosCaja(BaseModel):
    id_sucursal: int
    sucursal: str
    movimientos: list[MovimientoCajaReporte] = Field(default_factory=list)
    resumen_sucursal: ResumenSucursalMovimientosCaja


class TotalEmpresaMovimientosCaja(BaseModel):
    total_movimientos: int
    total_ingresos: float
    total_egresos: float


class MovimientosCajaEmpresaResponse(BaseModel):
    id_empresa: int
    fecha: date
    sucursales: list[SucursalMovimientosCaja]
    total_empresa: TotalEmpresaMovimientosCaja


class ReporteVentasParametrizadoRequest(BaseModel):
    fecha_inicial: date
    fecha_final: date
    id_sucursal: int | None = None
    id_tipo_venta: int | None = None
    id_metodo_pago: int | None = None
    id_producto: int | None = None
    id_usuario: int | None = None


class FiltrosAplicadosVentasResponse(BaseModel):
    periodo: str
    sucursal: str
    tipo_venta: str
    metodo_pago: str
    producto: str
    personal: str


class IndicadorReporteVentas(BaseModel):
    indicador: str
    valor: int | float


class DetalleAnaliticoVenta(BaseModel):
    id_venta: int
    numero_venta: str
    fecha_hora: str
    personal: str | None
    tipo: str | None
    metodo_pago: str | None
    productos: int
    total: float


class ReporteVentasParametrizadoResponse(BaseModel):
    id_empresa: int
    empresa: str
    fecha_generacion: str
    filtros_aplicados: FiltrosAplicadosVentasResponse
    resumen_gerencial: list[IndicadorReporteVentas]
    detalle_analitico: list[DetalleAnaliticoVenta]


class ReporteInventarioParametrizadoRequest(BaseModel):
    fecha_inicial: date
    fecha_final: date
    id_sucursal: int | None = None
    id_tipo_movimiento: int | None = None
    id_producto: int | None = None
    id_categoria_producto: int | None = None


class FiltrosAplicadosInventarioResponse(BaseModel):
    periodo: str
    sucursal: str
    tipo_movimiento: str
    producto: str
    categoria: str


class IndicadorReporteInventario(BaseModel):
    indicador: str
    valor: int | float


class DetalleAnaliticoInventario(BaseModel):
    id_movimiento_inventario: int
    numero_movimiento: str
    fecha_hora: str
    producto: str
    categoria: str | None
    tipo: str
    cantidad: int


class ReporteInventarioParametrizadoResponse(BaseModel):
    id_empresa: int
    empresa: str
    fecha_generacion: str
    filtros_aplicados: FiltrosAplicadosInventarioResponse
    resumen_gerencial: list[IndicadorReporteInventario]
    detalle_analitico: list[DetalleAnaliticoInventario]


class ReporteCajasParametrizadoRequest(BaseModel):
    fecha_inicial: date
    fecha_final: date
    id_sucursal: int | None = None
    id_caja: int | None = None
    id_tipo_movimiento_caja: int | None = None
    estado_sesion: str | None = None


class FiltrosAplicadosCajasResponse(BaseModel):
    periodo: str
    sucursal: str
    caja: str
    tipo_movimiento: str
    estado_sesion: str


class IndicadorReporteCajas(BaseModel):
    indicador: str
    valor: int | float


class DetalleAnaliticoCaja(BaseModel):
    id_movimiento_caja: int
    numero_movimiento: str
    fecha_hora: str
    caja: str
    tipo: str
    concepto: str | None
    monto: float


class ReporteCajasParametrizadoResponse(BaseModel):
    id_empresa: int
    empresa: str
    fecha_generacion: str
    filtros_aplicados: FiltrosAplicadosCajasResponse
    resumen_gerencial: list[IndicadorReporteCajas]
    detalle_analitico: list[DetalleAnaliticoCaja]
