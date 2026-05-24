from app.core.database import SessionLocal
from app.seeds.metodo_pago_seed import seed_metodos_pago
from app.seeds.roles_seed import seed_roles
from app.seeds.tipo_movimiento_caja_seed import seed_tipos_movimiento_caja
from app.seeds.tipo_movimiento_seed import seed_tipos_movimiento
from app.seeds.tipo_venta_seed import seed_tipos_venta


def run_seeds(db=None) -> None:
    own_session = db is None
    db = db or SessionLocal()
    try:
        seed_roles(db)
        seed_metodos_pago(db)
        seed_tipos_movimiento_caja(db)
        seed_tipos_movimiento(db)
        seed_tipos_venta(db)
        if own_session:
            db.commit()
    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()
