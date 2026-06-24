from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("SELECT * FROM notificaciones_historial")).mappings().all()
    print(f"Total: {len(res)}")
    for r in res:
        d = dict(r)
        payload = d.get("payload") or {}
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except Exception:
                pass
        tipo = payload.get("tipo", "")
        if "CREDITO" in tipo or d["tipo"] == "CREDITO" or "credito" in d["titulo"].lower():
            print(f"ID: {d['id']}, Empresa: {d['id_empresa']}, Titulo: {d['titulo']}, Mensaje: {d['mensaje']}, Payload: {payload}")
finally:
    db.close()
