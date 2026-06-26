from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.notifications.notifications import DispositivoToken, NotificacionHistorial
from app.core.database import SessionLocal


class NotificationRepository:
    @staticmethod
    def add_token(db: Session, token: str, uid_usuario: Optional[str] = None, rol: Optional[str] = None, plataforma: Optional[str] = None, id_empresa: Optional[int] = None):
        existing = db.query(DispositivoToken).filter(DispositivoToken.token == token).first()
        if existing:
            existing.uid_usuario = uid_usuario
            existing.rol = rol
            existing.plataforma = plataforma
            existing.id_empresa = id_empresa
            db.commit()
            db.refresh(existing)
            return existing
        obj = DispositivoToken(token=token, uid_usuario=uid_usuario, rol=rol, plataforma=plataforma, id_empresa=id_empresa)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_token(db: Session, token: str) -> bool:
        obj = db.query(DispositivoToken).filter(DispositivoToken.token == token).first()
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

    @staticmethod
    def list_tokens_by_empresa(db: Session, id_empresa: int) -> List[DispositivoToken]:
        return db.query(DispositivoToken).filter(DispositivoToken.id_empresa == id_empresa).all()

    @staticmethod
    def save_historial(db: Session, **data) -> NotificacionHistorial:
        # Use a dedicated short-lived session for historial so failures
        # here don't abort the caller's transaction.
        session = SessionLocal()
        try:
            obj = NotificacionHistorial(**data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def mark_read(db: Session, notif_id: int):
        result = db.execute(
            text("UPDATE notificaciones_historial SET leido = TRUE WHERE id = :notif_id RETURNING id"),
            {"notif_id": notif_id},
        ).first()
        db.commit()
        return result
