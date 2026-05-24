from typing import List, Dict, Any, Optional
from app.repositories.notification_repository import NotificationRepository
from app.core.firebase_admin_client import get_messaging_client
from sqlalchemy.orm import Session
from firebase_admin import messaging as fb_messaging


class NotificationService:
    @staticmethod
    def enviar_alerta(db: Session, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None, tokens: Optional[List[str]] = None):
        # Persist historial (guardado seguro: captura errores de DB y evita propagar excepciones)
        try:
            historial = NotificationRepository.save_historial(db, id_empresa=id_empresa, tipo="ALERTA", titulo=titulo, mensaje=mensaje, payload=payload or {})
        except Exception:
            # If persisting the historial fails, do not abort the caller flow; return a noop result.
            return {"sent": 0, "historial_id": None}

        # Prepare messages
        tokens = tokens or [t.token for t in NotificationRepository.list_tokens_by_empresa(db, id_empresa)]
        if not tokens:
            return {"sent": 0, "historial_id": historial.id}

        messaging = get_messaging_client()
        if not messaging:
            # no firebase credentials configured; skip actual send
            return {"sent": 0, "historial_id": historial.id}

        batch = []
        for t in tokens:
            msg = fb_messaging.Message(
                token=t,
                notification=fb_messaging.Notification(title=titulo, body=mensaje),
                data={"payload": str(payload or {})},
            )
            batch.append(msg)

        # send_all expects a list of messages
        try:
            result = fb_messaging.send_all(batch)
            # handle failures (could remove tokens) - simple count
            return {"sent": result.success_count, "failed": result.failure_count, "historial_id": historial.id}
        except Exception:
            return {"sent": 0, "historial_id": historial.id}
