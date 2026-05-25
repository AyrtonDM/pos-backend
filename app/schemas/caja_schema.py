from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.movimiento_caja_schema import MovimientoCajaResponse


class CajaCreate(BaseModel):
    nombre: str
    codigo: str


class CajaUpdate(BaseModel):
    nombre: str
    codigo: str
    activo: bool


class CajaResponse(BaseModel):
    id_caja: int
    id_sucursal: int
    nombre: str
    codigo: str
    fecha_creacion: date
    activo: bool

    class Config:
        from_attributes = True


class CajaSesionCreate(BaseModel):
    monto_inicial: Decimal
    nota: str | None = None


class CajaCierreDetalleCreate(BaseModel):
    id_metodo_pago: int
    monto_esperado: Decimal
    monto_real: Decimal
    diferencia: Decimal
    observacion: str | None = None


class CajaCierreDetalleResponse(BaseModel):
    id_caja_cierre_detalle: int
    id_metodo_pago: int
    id_caja_sesion: int
    monto_esperado: Decimal
    monto_real: Decimal
    diferencia: Decimal
    observacion: str | None

    class Config:
        from_attributes = True


class CajaSesionResponse(BaseModel):
    id_caja_sesion: int
    id_caja: int
    id_usuario: int
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    monto_inicial: Decimal
    monto_final: Decimal | None
    estado: str
    nota: str | None

    class Config:
        from_attributes = True


class CajaSesionCierreResponse(BaseModel):
    id_caja_sesion: int
    monto_inicial: Decimal
    monto_total_real: Decimal
    monto_final: Decimal
    estado: str
    fecha_cierre: datetime
    movimiento_cierre: list[MovimientoCajaResponse]
    cierres: list[CajaCierreDetalleResponse]

    class Config:
        from_attributes = True


class MovimientoCajaPorMetodoPagoResponse(BaseModel):
    id_metodo_pago: int | None
    metodo_pago: str | None
    total_ingresos: Decimal
    total_egresos: Decimal
    monto_esperado: Decimal
    movimientos: list[MovimientoCajaResponse]


class ResumenMovimientosCajaResponse(BaseModel):
    id_caja_sesion: int
    monto_esperado_total: Decimal
    resumen_por_metodo_pago: list[MovimientoCajaPorMetodoPagoResponse]
