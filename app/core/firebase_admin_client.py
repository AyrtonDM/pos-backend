import os
from typing import Optional
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

#def get_messaging_client() -> Optional[messaging]:

def get_messaging_client() -> Optional[Any]:
    global _app
    if _app is None:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if not cred_path or not os.path.exists(cred_path):
            cred_path = _find_service_account_in_secrets()
        if not cred_path or not os.path.exists(cred_path):
            print("Firebase service account not found. Set FIREBASE_SERVICE_ACCOUNT or place JSON in app/secrets")
            return None
        cred = credentials.Certificate(cred_path)
        _app = initialize_app(cred)
        print(f"Initialized firebase-admin with {cred_path}")
    return messaging
