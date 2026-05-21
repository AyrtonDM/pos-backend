from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.database import SessionLocal
from app.core.schema_updates import apply_schema_updates
from app.models.clientes import CategoriaCliente, Cliente
from app.models.empresas import Caja, CajaSesion, Empresa, Sucursal
from app.models.inventario import MovimientoInventario, Stock, TipoMovimiento
from app.models.productos import CategoriaProducto, Producto, SubcategoriaProducto
from app.models.usuarios import Persona, Rol, Usuario, UsuarioRol
from app.routers.cliente_router import categoria_cliente_router, cliente_router
from app.routers.empresa_router import router as empresa_router
from app.routers.auth_router import router as auth_router
from app.routers.inventario_router import router as inventario_router
from app.routers.producto_router import router as producto_router
from app.routers.sucursal_router import (
    caja_router,
    empresa_router as sucursal_empresa_router,
    invitacion_router,
    sucursal_router,
)
from app.seeds import run_seeds
from app.services.inventario_service import InventarioService

app = FastAPI(title="POS Backend")

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
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
app.include_router(empresa_router)
app.include_router(inventario_router)
app.include_router(producto_router)
app.include_router(caja_router)
app.include_router(sucursal_empresa_router)
app.include_router(sucursal_router)
app.include_router(invitacion_router)

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
        run_seeds(db)
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
