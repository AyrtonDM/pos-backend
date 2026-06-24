import os
from typing import Optional, Any
from pathlib import Path

from firebase_admin import credentials, initialize_app, messaging, get_app

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


def get_messaging_client() -> Optional[Any]:
    global _app
    try:
        _app = get_app()
        print(f"[FIREBASE] App ya inicializado correctamente")
    except ValueError:
        print(f"[FIREBASE] Inicializando Firebase Admin SDK...")
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        print(f"   Buscando credenciales en: {cred_path}")
        if not cred_path or not os.path.exists(cred_path):
            print(f"   [INFO] No encontrado en variable de entorno, buscando en app/secrets/")
            cred_path = _find_service_account_in_secrets()
        
        if not cred_path or not os.path.exists(cred_path):
            print(f"[FIREBASE] Archivo de credenciales NO encontrado!")
            print(f"   - Verifica FIREBASE_SERVICE_ACCOUNT en .env")
            print(f"   - O coloca un archivo .json en app/secrets/")
            return None
        
        try:
            print(f"   Leyendo credenciales desde: {cred_path}")
            cred = credentials.Certificate(cred_path)
            _app = initialize_app(cred)
            print(f"[FIREBASE] Inicializado exitosamente con {cred_path}")
        except Exception as e:
            print(f"[FIREBASE] Error al inicializar: {str(e)}")
            return None
    
    return messaging
