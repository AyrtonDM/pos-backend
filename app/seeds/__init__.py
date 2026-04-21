from app.core.database import SessionLocal
from app.seeds.roles_seed import seed_roles
from app.seeds.tipo_movimiento_seed import seed_tipos_movimiento


def run_seeds(db=None) -> None:
    own_session = db is None
    db = db or SessionLocal()
    try:
        seed_roles(db)
        seed_tipos_movimiento(db)
        if own_session:
            db.commit()
    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()
