import os
from typing import Optional, Any
from pathlib import Path

from firebase_admin import credentials, initialize_app, messaging

_app = None


def _find_service_account_in_secrets() -> Optional[str]:
    # look for any .json inside app/secrets
    base = Path(__file__).resolve().parents[1] / "secrets"
    if not base.exists():
        return None
    for p in base.iterdir():
        if p.is_file() and p.suffix.lower() == ".json":
            return str(p)
    return None

# def get_messaging_client() -> Optional[messaging]:

def get_messaging_client() -> Optional[Any]:
    global _app
    if _app is None:
        # Buscar credenciales en orden secuencial:
        # a) FIREBASE_SERVICE_ACCOUNT
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        # b) FIREBASE_CREDENTIALS_PATH
        if not cred_path or not os.path.exists(cred_path):
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            
        # c) app/secrets/*.json
        if not cred_path or not os.path.exists(cred_path):
            cred_path = _find_service_account_in_secrets()

        if not cred_path or not os.path.exists(cred_path):
            print(
                "[FCM] Opcional: No se encontró el archivo de credenciales de Firebase. "
                "Las notificaciones push FCM no se enviarán, pero el backend continuará funcionando. "
                "Defina FIREBASE_SERVICE_ACCOUNT/FIREBASE_CREDENTIALS_PATH o coloque un archivo JSON en app/secrets.",
                flush=True
            )
            return None

        try:
            cred = credentials.Certificate(cred_path)
            _app = initialize_app(cred)
            print(f"[FCM] Firebase Admin inicializado exitosamente con {cred_path}", flush=True)
        except Exception as e:
            print(f"[FCM] Error crítico al inicializar app de Firebase: {e}", flush=True)
            return None

    return messaging
