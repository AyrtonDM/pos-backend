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
            historial = NotificationRepository.save_historial(
                db, id_empresa=id_empresa, tipo="ALERTA", titulo=titulo, mensaje=mensaje, payload=payload or {}
            )
        except Exception as e:
            print(f"[FCM] Error al guardar historial: {e}", flush=True)
            return {"sent": 0, "historial_id": None}

        # Prepare tokens
        resolved_tokens = tokens or [t.token for t in NotificationRepository.list_tokens_by_empresa(db, id_empresa)]
        print(f"[FCM] Tokens a notificar para empresa {id_empresa}: {len(resolved_tokens)}", flush=True)
        for idx, tok in enumerate(resolved_tokens):
            print(f"[FCM]   Token[{idx}]: {tok[:25]}...", flush=True)

        if not resolved_tokens:
            print(f"[FCM] Sin tokens registrados para empresa {id_empresa}. Push no enviado.", flush=True)
            return {"sent": 0, "historial_id": historial.id}

        messaging = get_messaging_client()
        if messaging is None:
            print("[FCM] Firebase no inicializado. Se omite envío de notificaciones push.", flush=True)
            return {"sent": 0, "failed": 0, "reason": "firebase_not_initialized", "historial_id": historial.id}

        # Build data dict with all string values (FCM requires strings)
        data_payload: Dict[str, str] = {}
        if payload:
            for k, v in payload.items():
                data_payload[k] = str(v)

        # Build batch with AndroidConfig for sound + high priority + channel
        batch = []
        for t in resolved_tokens:
            msg = fb_messaging.Message(
                token=t,
                notification=fb_messaging.Notification(title=titulo, body=mensaje),
                data=data_payload,
                android=fb_messaging.AndroidConfig(
                    priority="high",
                    notification=fb_messaging.AndroidNotification(
                        channel_id="credit_payments_channel",
                        sound="default",
                        default_sound=True,
                        default_vibrate_timings=True,
                        notification_priority=fb_messaging.AndroidNotificationPriority.PRIORITY_HIGH,
                    ),
                ),
            )
            batch.append(msg)

        try:
            result = fb_messaging.send_all(batch)
            print(f"[FCM] Firebase resultado → success={result.success_count}, failed={result.failure_count}", flush=True)

            for idx, response in enumerate(result.responses):
                if not response.success:
                    token_to_remove = resolved_tokens[idx]
                    exc = response.exception
                    print(f"[FCM] Fallo en token[{idx}] ({token_to_remove[:25]}...): {exc}", flush=True)

                    is_unregistered = False
                    if exc:
                        exc_code = getattr(exc, 'code', '') or ''
                        exc_name = exc.__class__.__name__
                        if (
                            'unregistered' in exc_code.lower()
                            or 'unregistered' in exc_name.lower()
                            or exc_code == 'messaging/registration-token-not-registered'
                            or 'invalid' in exc_code.lower()
                            or 'invalid' in exc_name.lower()
                        ):
                            is_unregistered = True

                    if is_unregistered:
                        try:
                            NotificationRepository.delete_token(db, token_to_remove)
                            print(f"[FCM] Token obsoleto eliminado: {token_to_remove[:25]}...", flush=True)
                        except Exception as delete_err:
                            print(f"[FCM] Error eliminando token obsoleto: {delete_err}", flush=True)

            return {"sent": result.success_count, "failed": result.failure_count, "historial_id": historial.id}

        except Exception as e:
            print(f"[FCM] Error crítico en send_all: {e}", flush=True)
            return {"sent": 0, "historial_id": historial.id}

    @staticmethod
    def enviar_notificacion_usuario(db: Session, id_usuario: int, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None):
        """
        Envia una notificacion a todos los dispositivos registrados de un usuario especifico de la empresa.
        """
        try:
            from app.models.notifications.notifications import DispositivoToken
            tokens_query = db.query(DispositivoToken).filter(
                DispositivoToken.uid_usuario == str(id_usuario),
                DispositivoToken.id_empresa == id_empresa
            ).all()
            tokens_list = [t.token for t in tokens_query]
            
            return NotificationService.enviar_alerta(
                db=db,
                id_empresa=id_empresa,
                titulo=titulo,
                mensaje=mensaje,
                payload=payload,
                tokens=tokens_list
            )
        except Exception as e:
            print(f"[FCM] Error al enviar notificacion a usuario {id_usuario}: {e}", flush=True)
            return {"sent": 0, "failed": 0, "error": str(e)}
