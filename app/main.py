from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.database import SessionLocal
from app.core.schema_updates import apply_schema_updates
from app.models.clientes import CategoriaCliente, Cliente
from app.models.empresas import (
    Caja,
    CajaCierreDetalle,
    CajaSesion,
    Empresa,
    MovimientoCaja,
    Sucursal,
    TipoMovimientoCaja,
)
from app.models.inventario import MovimientoInventario, Stock, TipoMovimiento
from app.models.productos import CategoriaProducto, Producto, SubcategoriaProducto
from app.models.usuarios import Persona, Rol, Usuario, UsuarioRol, Modulo, Permiso, RolPermiso
from app.models.ventas import CuentaPorCobrar, MetodoPago, PagoCredito, TipoVenta, Venta, VentaPago
from app.routers.cliente_router import categoria_cliente_router, cliente_router
from app.routers.empresa_router import router as empresa_router
from app.routers.auth_router import router as auth_router
from app.routers.inventario_router import router as inventario_router
from app.routers.rol_router import router as rol_router
from app.routers.producto_router import router as producto_router
from app.routers.reportes_router import router as reportes_router
from app.routers.venta_router import venta_router
from app.routers.empresa_tipo_movimiento_caja_router import tipo_movimiento_caja_router
from app.routers.sucursal_router import (
    caja_router,
    empresa_router as sucursal_empresa_router,
    invitacion_router,
    sucursal_router,
)
from app.routers.notifications_router import router as notifications_router
from app.routers.pago_router import router as pago_router
from app.routers.plan_router import router as plan_router
from app.seeds import run_seeds
from app.services.inventario_service import InventarioService
from app.websockets.administrador import router as administrador_websocket_router

app = FastAPI(title="POS Backend")

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://pos-frontend.duckdns.org"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(categoria_cliente_router)
app.include_router(cliente_router)
app.include_router(tipo_movimiento_caja_router)
app.include_router(rol_router)
app.include_router(empresa_router)
app.include_router(inventario_router)
app.include_router(producto_router)
app.include_router(venta_router)
app.include_router(caja_router)
app.include_router(sucursal_empresa_router)
app.include_router(sucursal_router)
app.include_router(invitacion_router)
app.include_router(notifications_router)
app.include_router(reportes_router)
app.include_router(pago_router)
app.include_router(plan_router)
app.include_router(administrador_websocket_router)

media_root = Path(__file__).resolve().parent / "media"
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_root), name="media")

@app.on_event("startup")
def on_startup() -> None:
    # Importing models above registers all mapped tables in Base.metadata.
    Base.metadata.create_all(bind=engine)
    apply_schema_updates()
    db = SessionLocal()
    try:
        # run_seeds(db)
        InventarioService.sincronizar_stocks_iniciales(db=db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
