import os
from typing import Optional, Any
from pathlib import Path

from firebase_admin import credentials, initialize_app, messaging, get_app
import firebase_admin

_app = None


def _find_service_account_in_secrets() -> Optional[str]:
    """Busca cualquier archivo .json dentro de app/secrets/."""
    base = Path(__file__).resolve().parents[1] / "secrets"
    print(f"[FCM] Buscando credenciales en directorio: {base}", flush=True)
    if not base.exists():
        print(f"[FCM] Directorio app/secrets/ no existe: {base}", flush=True)
        return None
    for p in base.iterdir():
        if p.is_file() and p.suffix.lower() == ".json":
            print(f"[FCM] Credencial encontrada en app/secrets/: {p.name}", flush=True)
            return str(p)
    print(f"[FCM] No se encontró ningún .json en app/secrets/", flush=True)
    return None


def get_messaging_client() -> Optional[Any]:
    global _app

    # Si ya fue inicializado, retornar directamente
    if _app is not None:
        return messaging

    print("[FCM] Inicializando Firebase Admin SDK...", flush=True)

    # a) FIREBASE_SERVICE_ACCOUNT
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if cred_path:
        print(f"[FCM] FIREBASE_SERVICE_ACCOUNT apunta a: {cred_path}", flush=True)
        if not os.path.exists(cred_path):
            print(f"[FCM] ADVERTENCIA: el archivo indicado por FIREBASE_SERVICE_ACCOUNT NO existe: {cred_path}", flush=True)
            cred_path = None
    else:
        print("[FCM] Variable FIREBASE_SERVICE_ACCOUNT no definida.", flush=True)

    # b) FIREBASE_CREDENTIALS_PATH
    if not cred_path:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path:
            print(f"[FCM] FIREBASE_CREDENTIALS_PATH apunta a: {cred_path}", flush=True)
            if not os.path.exists(cred_path):
                print(f"[FCM] ADVERTENCIA: el archivo indicado por FIREBASE_CREDENTIALS_PATH NO existe: {cred_path}", flush=True)
                cred_path = None
        else:
            print("[FCM] Variable FIREBASE_CREDENTIALS_PATH no definida.", flush=True)

    # c) app/secrets/*.json
    if not cred_path:
        cred_path = _find_service_account_in_secrets()

    if not cred_path or not os.path.exists(cred_path):
        print(
            "[FCM] No se encontró ningún archivo de credenciales de Firebase. "
            "Las notificaciones push FCM no se enviarán. "
            "Define FIREBASE_SERVICE_ACCOUNT o coloca el JSON en app/secrets/.",
            flush=True,
        )
        return None

    print(f"[FCM] Usando credencial: {cred_path}", flush=True)

    try:
        cred = credentials.Certificate(cred_path)
        _app = initialize_app(cred)
        print(f"[FCM] Firebase Admin inicializado exitosamente", flush=True)
    except ValueError as ve:
        # initialize_app() lanza ValueError si ya hay una app por defecto
        print(f"[FCM] Firebase ya estaba inicializado (posible reimport): {ve}", flush=True)
        try:
            _app = get_app()
        except Exception:
            pass
    except Exception as e:
        print(f"[FCM] Error al inicializar Firebase Admin: {e}", flush=True)
        return None

    return messaging

