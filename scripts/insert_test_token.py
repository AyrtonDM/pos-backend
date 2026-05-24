from app.core.database import SessionLocal
from app.repositories.notification_repository import NotificationRepository


def run():
    db = SessionLocal()
    try:
        token = "TEST_FCM_TOKEN_REPLACE_ME"
        obj = NotificationRepository.add_token(db=db, token=token, uid_usuario="test-user", plataforma="web", id_empresa=1)
        print("Inserted token id:", obj.id)
    finally:
        db.close()


if __name__ == "__main__":
    run()
