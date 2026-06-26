from typing import List, Dict, Any, Optional
from app.repositories.notification_repository import NotificationRepository
from app.core.firebase_admin_client import get_messaging_client
from sqlalchemy.orm import Session
from firebase_admin import messaging as fb_messaging


class NotificationService:
    @staticmethod
    def enviar_alerta(db: Session, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None, tokens: Optional[List[str]] = None):
        # 1. Guardar historial antes de intentar Firebase
        try:
            historial = NotificationRepository.save_historial(
                db, id_empresa=id_empresa, tipo="ALERTA", titulo=titulo, mensaje=mensaje, payload=payload or {}
            )
            print("[FCM] historial guardado", flush=True)
        except Exception as e:
            print(f"[FCM] Error al guardar historial: {e}", flush=True)
            return {"sent": 0, "historial_id": None}

        # 2. Obtener/resolver tokens
        resolved_tokens = tokens or [t.token for t in NotificationRepository.list_tokens_by_empresa(db, id_empresa)]
        print(f"[FCM] tokens encontrados: {len(resolved_tokens)}", flush=True)
        for idx, tok in enumerate(resolved_tokens):
            print(f"[FCM]   Token[{idx}]: {tok[:25]}...", flush=True)

        # Si no hay tokens, retornar pero después de guardar historial
        if not resolved_tokens:
            print(f"[FCM] Sin tokens registrados para empresa {id_empresa}. Push no enviado.", flush=True)
            return {"sent": 0, "historial_id": historial.id}

        # 3. Inicializar Firebase
        messaging = get_messaging_client()
        # Si Firebase no inicializa, retornar pero después de guardar historial
        if messaging is None:
            print("[FCM] Firebase no inicializado. Se omite envío de notificaciones push.", flush=True)
            return {"sent": 0, "failed": 0, "reason": "firebase_not_initialized", "historial_id": historial.id}

        # 4. Build data dict with all string values (FCM requires strings)
        data_payload: Dict[str, str] = {}
        if payload:
            for k, v in payload.items():
                data_payload[k] = str(v)

        success_count = 0
        failure_count = 0

        for idx, t in enumerate(resolved_tokens):
            token_prefix = t[:25]
            print(f"[FCM] Enviando a token[{idx}] ({token_prefix}...)", flush=True)
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
            try:
                message_id = messaging.send(msg)
                success_count += 1
                print(f"[FCM] firebase success en token[{idx}]: id={message_id}", flush=True)
            except Exception as exc:
                failure_count += 1
                print(f"[FCM] Fallo en token[{idx}] ({token_prefix}...): {exc}", flush=True)

                is_unregistered = False
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
                        NotificationRepository.delete_token(db, t)
                        print(f"[FCM] Token obsoleto eliminado: {token_prefix}...", flush=True)
                    except Exception as delete_err:
                        print(f"[FCM] Error eliminando token obsoleto: {delete_err}", flush=True)

        print(f"[FCM] firebase success={success_count}, failed={failure_count}", flush=True)
        return {"sent": success_count, "failed": failure_count, "historial_id": historial.id}

    @staticmethod
    def enviar_notificacion_usuario(db: Session, id_usuario: int, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None):
        """
        Envia una notificacion a todos los dispositivos registrados de un usuario especifico de la empresa.
        """
        try:
            from app.models.notifications.notifications import DispositivoToken
            tokens_query = db.query(DispositivoToken).filter(
                DispositivoToken.uid_usuario == str(id_usuario)
            ).all()
            tokens_list = list({t.token for t in tokens_query if t.token})
            
            print(f"[FCM USUARIO] id_usuario={id_usuario}", flush=True)
            print(f"[FCM USUARIO] empresa_evento={id_empresa}", flush=True)
            print(f"[FCM USUARIO] tokens encontrados={len(tokens_list)}", flush=True)
            for idx, tok in enumerate(tokens_list):
                print(f"[FCM USUARIO]   Token[{idx}]: {tok[:25]}...", flush=True)
            
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
