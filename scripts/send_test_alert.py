from app.core.database import SessionLocal
from app.services.notification_service import NotificationService


def run():
    db = SessionLocal()
    try:
        res = NotificationService.enviar_alerta(db=db, id_empresa=1, titulo="Prueba alerta", mensaje="Stock bajo en producto X", payload={"producto_id": 123})
        print(res)
    finally:
        db.close()


if __name__ == "__main__":
    run()
