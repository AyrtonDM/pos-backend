from typing import List, Dict, Any, Optional
from app.repositories.notification_repository import NotificationRepository
from app.core.firebase_admin_client import get_messaging_client
from app.models.notifications.notifications import DispositivoToken
from sqlalchemy.orm import Session
from firebase_admin import messaging as fb_messaging

# Memory buffer for diagnostic logs
fcm_logs = []

def log_fcm(msg: str):
    fcm_logs.append(msg)
    if len(fcm_logs) > 200:
        fcm_logs.pop(0)
    print(msg)


class NotificationService:
    @staticmethod
    def enviar_alerta(db: Session, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None, tokens: Optional[List[str]] = None):
        log_fcm(f"\n[ALERTA] Iniciando envio de alerta para empresa {id_empresa}")
        log_fcm(f"   Titulo: {titulo}")
        log_fcm(f"   Mensaje: {mensaje}")
        
        # Persist historial
        try:
            historial = NotificationRepository.save_historial(db, id_empresa=id_empresa, tipo="ALERTA", titulo=titulo, mensaje=mensaje, payload=payload or {})
            log_fcm(f"   [OK] Historial guardado con ID: {historial.id}")
        except Exception as e:
            log_fcm(f"   [FAIL] Error al guardar historial: {str(e)}")
            return {"sent": 0, "historial_id": None}

        # Prepare messages
        if tokens is None:
            tokens_db = NotificationRepository.list_tokens_by_empresa(db, id_empresa)
            tokens = [t.token for t in tokens_db]
            log_fcm(f"   [INFO] Tokens recuperados de BD: {len(tokens)}")
        else:
            log_fcm(f"   [INFO] Tokens proporcionados directamente: {len(tokens)}")
        
        log_fcm(f"[FIND] Intentando enviar alerta para empresa {id_empresa}. Tokens encontrados: {tokens}")
        if not tokens:
            log_fcm(f"   [WARNING] No hay tokens para esta empresa")
            return {"sent": 0, "historial_id": historial.id}

        messaging = get_messaging_client()
        if not messaging:
            log_fcm("   [FAIL] Firebase Admin SDK no inicializado")
            return {"sent": 0, "historial_id": historial.id}

        log_fcm(f"   [OK] Cliente Firebase disponible")
        
        batch = []
        for t in tokens:
            if t.startswith("mock_token"):
                log_fcm(f"      [SKIP] Ignorando token mock: {t[:30]}...")
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

        log_fcm(f"   [BATCH] Batch preparado con {len(batch)} mensajes")
        
        if not batch:
            log_fcm("   [WARNING] No hay mensajes validos (todos eran mocks) en el batch")
            return {"sent": 0, "historial_id": historial.id}

        try:
            log_fcm(f"   [SEND] Enviando batch a Firebase...")
            result = fb_messaging.send_each(batch)
            log_fcm(f"[SUCCESS] Alerta enviada para empresa {id_empresa}. Enviados: {result.success_count}, Fallidos: {result.failure_count}")
            if result.failure_count > 0:
                log_fcm(f"   Fallos en respuestas:")
                for i, resp in enumerate(result.responses):
                    if not resp.success:
                        log_fcm(f"      {i}. Error: {resp.exception}")
            return {"sent": result.success_count, "failed": result.failure_count, "historial_id": historial.id}
        except Exception as e:
            log_fcm(f"[FAIL] Error critico al invocar Firebase en enviar_alerta: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"sent": 0, "historial_id": historial.id}

    @staticmethod
    def enviar_notificacion_usuario(db: Session, id_usuario: int, id_empresa: int, titulo: str, mensaje: str, payload: Optional[Dict[str, Any]] = None):
        log_fcm(f"\n[USER] Iniciando envio para usuario {id_usuario} en empresa {id_empresa}")
        log_fcm(f"   Titulo: {titulo}")
        log_fcm(f"   Mensaje: {mensaje}")
        
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
            log_fcm(f"   [OK] Historial guardado con ID: {historial.id}")
        except Exception as e:
            log_fcm(f"   [FAIL] Error al guardar historial: {str(e)}")
            return {"sent": 0, "historial_id": None}

        # Fetch tokens of the specific user
        tokens = [t.token for t in db.query(DispositivoToken).filter(DispositivoToken.uid_usuario == str(id_usuario)).all()]
        log_fcm(f"[FIND] Encontrados para usuario {id_usuario}: {len(tokens)} token(s)")
        if tokens:
            for i, tok in enumerate(tokens, 1):
                log_fcm(f"      {i}. {tok[:30]}...")
        
        if not tokens:
            log_fcm(f"   [WARNING] No hay tokens registrados para este usuario")
            return {"sent": 0, "historial_id": historial.id}

        messaging = get_messaging_client()
        if not messaging:
            log_fcm("   [FAIL] Firebase Admin SDK no inicializado")
            return {"sent": 0, "historial_id": historial.id}

        log_fcm(f"   [OK] Cliente Firebase disponible")

        batch = []
        for t in tokens:
            if t.startswith("mock_token"):
                log_fcm(f"      [SKIP] Ignorando token mock: {t[:30]}...")
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

        log_fcm(f"   [BATCH] Batch preparado con {len(batch)} mensajes")
        
        if not batch:
            log_fcm(f"   [WARNING] No hay mensajes validos (todos eran mocks) para usuario {id_usuario}")
            return {"sent": 0, "historial_id": historial.id}

        try:
            log_fcm(f"   [SEND] Enviando batch a Firebase...")
            result = fb_messaging.send_each(batch)
            log_fcm(f"[SUCCESS] Notificacion enviada para usuario {id_usuario}. Enviados: {result.success_count}, Fallidos: {result.failure_count}")
            if result.failure_count > 0:
                log_fcm(f"   Fallos en respuestas:")
                for i, resp in enumerate(result.responses):
                    if not resp.success:
                        log_fcm(f"      {i}. Error: {resp.exception}")
            return {"sent": result.success_count, "failed": result.failure_count, "historial_id": historial.id}
        except Exception as e:
            log_fcm(f"[FAIL] Error critico al invocar Firebase: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"sent": 0, "historial_id": historial.id}
