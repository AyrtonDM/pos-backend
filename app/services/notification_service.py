from typing import List, Dict, Any, Optional
from app.repositories.notification_repository import NotificationRepository
from app.core.firebase_admin_client import get_messaging_client
from app.models.notifications.notifications import DispositivoToken
from sqlalchemy.orm import Session
from firebase_admin import messaging as fb_messaging


class NotificationService:
    @staticmethod
    def enviar_alerta(db: Session, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None, tokens: Optional[List[str]] = None):
        # Persist historial
        try:
            historial = NotificationRepository.save_historial(db, id_empresa=id_empresa, tipo="ALERTA", titulo=titulo, mensaje=mensaje, payload=payload or {})
        except Exception:
            return {"sent": 0, "historial_id": None}

        # Prepare messages
        if tokens is None:
            tokens_db = NotificationRepository.list_tokens_by_empresa(db, id_empresa)
            tokens = [t.token for t in tokens_db]
        
        if not tokens:
            return {"sent": 0, "historial_id": historial.id}

        messaging = get_messaging_client()
        if not messaging:
            return {"sent": 0, "historial_id": historial.id}
        
        batch = []
        for t in tokens:
            if t.startswith("mock_token"):
                continue
            msg = fb_messaging.Message(
                token=t,
                notification=fb_messaging.Notification(title=titulo, body=mensaje),
                data={
                    "payload": str(payload or {}),
                    "id_empresa": str(id_empresa)
                },
            )
            batch.append(msg)
        
        if not batch:
            return {"sent": 0, "historial_id": historial.id}

        try:
            result = fb_messaging.send_each(batch)
            return {"sent": result.success_count, "failed": result.failure_count, "historial_id": historial.id}
        except Exception as e:
            print(f"[FCM ALERT SEND ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {"sent": 0, "historial_id": historial.id}

    @staticmethod
    def enviar_notificacion_usuario(db: Session, id_usuario: int, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None):
        # Persist historial
        try:
            full_payload = dict(payload or {})
            full_payload["id_usuario"] = id_usuario
            historial = NotificationRepository.save_historial(
                db, 
                id_empresa=id_empresa, 
                tipo="ALERTA", 
                titulo=titulo, 
                mensaje=mensaje, 
                payload=full_payload,
                leido=False
            )
        except Exception:
            return {"sent": 0, "historial_id": None}

        # Fetch tokens of the specific user
        tokens = [t.token for t in db.query(DispositivoToken).filter(DispositivoToken.uid_usuario == str(id_usuario)).all()]
        
        if not tokens:
            return {"sent": 0, "historial_id": historial.id}

        messaging = get_messaging_client()
        if not messaging:
            return {"sent": 0, "historial_id": historial.id}

        batch = []
        for t in tokens:
            if t.startswith("mock_token"):
                continue
            msg = fb_messaging.Message(
                token=t,
                notification=fb_messaging.Notification(title=titulo, body=mensaje),
                data={
                    "payload": str(payload or {}),
                    "id_empresa": str(id_empresa)
                },
            )
            batch.append(msg)
        
        if not batch:
            return {"sent": 0, "historial_id": historial.id}

        try:
            result = fb_messaging.send_each(batch)
            return {"sent": result.success_count, "failed": result.failure_count, "historial_id": historial.id}
        except Exception as e:
            print(f"[FCM SEND ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {"sent": 0, "historial_id": historial.id}
