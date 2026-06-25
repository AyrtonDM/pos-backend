import os
from typing import Optional, Any
from firebase_admin import credentials, initialize_app, messaging, get_app

_app = None

def get_messaging_client() -> Optional[Any]:
    global _app
    try:
        # Si Firebase ya está corriendo en la instancia actual, lo recupera
        _app = get_app()
    except ValueError:
        try:
            print("[FIREBASE] Forzando inicialización directa e inline desde código...")
            
            # 🔥 Credenciales unificadas e indestructibles con tus datos reales
            firebase_config = {
                "type": "service_account",
                "project_id": "pos-si2",
                "private_key_id": "7cfc93deac2df9a32ba98c15e60ada086ee47efc",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDjlUYzxsUMx8lE\nuag+Oo9FCVeTuGHtzdJYg6DrdmYWE6/GOaQ2E4M51pdNL6ZZI4178UFMfGSF9g3r\nTGD0jsoNGSjez7BPyEJAhwQSwukJUHK5G2agUSOm5ieuTMGEdjV+Hvif47+XRnch\nge4HqCXOlCnKwWYLy1CVZW3Bzep3Sb7XqEEg0uNw71BjwjJNls5iYWz+MvpdEs4J\nQz8kQ+jg/2oUgzR1iHeibZhAcfDI3MGWMKn7jORcWs1y/Tx2iJRApvaUXFVc0gCF\nfTA969PouLf0kJwsubPcfNGaxDqBod4z9EkdLo+HJofLpgOzgi5zgTfjMBePbQsu\nQFM9lxr7AgMBAAECggEAXbzCvRm+WNzDRCjaKMNy9mL6LPBxeYLghC+3LLTIKIi0\nSge84L8Zuk1uZU7ei/GOWYINvMSxnNGzevqrJp/XjhySTm+p9bqMu0pBPb8FQB5g\nGmk0VI0HC7vZlTutK3OK5ec4zZZ/d/4AnI8JLSMva05whkAxWWNFTjuIQR6g17+D\nxLGWePEmaOpxnY3DVu9mM9rWJFgRXUdIok7rkFOOHnmIAvq49Q0vfw1tHq8g+mel\nYfU0UXh9KEoWZjFNq6CD95b+ldwYgNk88wCQ4yVSWfzAUJFj57HGn1uPa9CR4pFX\nrcY6jdSiC8rGQGLvPUT/4kOpK3n/RZFyM/sZSwvFuQKBgQD5yCfiKk/tE/FwBgoo\nXcOudi9qpFSsNF5YpJrzf2RoZ8uHTrbgyDmV2zGS8zaT4gsqJxBRwVL6vPTf3WB6\n34gHJqEkmK6r3am2POCNrSYdarqVeb+FrzkEMID7cEmGeRUTAcUOP/E5SrB5T6GF\nVCSVtGaq9aLxoUIP1mgnzCnH6QKBgQDpP6WrRN65UzrEQs9TxBtmL3kJscuMl5LO\nZvYhRKsqjN2novPcTCjrAPLaEaNnKuC17tHV3eAJ2b/bJ6HGQHTPzzhLwYvBEumC\ncu7Zz6lzhjzlN2KfCC1kXV3IQlmblnLacd+jmjOrWVOihQ3G7Ra2q4YoneojjJ7d\nuKbdodThQwKBgA8arma7vkeMzC3E/7o/KUUUenuNYl1jcU0U7xXIX078787H0ME4\n+lp4fb/wGx3ILnqnEBKRiS4GXRxoa5wihjxAdsAax303Ezsk5UNL9CEVQiEl0pIH\n7X+2WyZZPOj3y3FxyvO4pCKdxJwhV5gTZX70AL1XyzmnUbJZecTmUKR5AoGBANMu\nvkfgVivDcJzLxL2Z/Bi7+MHPSXVksxXP4R9j9fnTisjB4DtgdVe5Byhr+d9p0gTH\nUxNpDPS+Q1ggfPdr2pdgjh8BARDxl5x1hU6OF2UycCY0zEUi+T46zrOHZ2xYfmrL\n2WleL1P/z5qBD2VBumPvzsstlxVSt3AWRHa8lGrTAoGAWnhRqXHDWce5x5aqwI/C\naS00JVbQnX9x/tQNWtuJQMpVqkKeasYdTPoGhfG0d6J3PSC/Hj28CMElNTJw7rBl\neN21X3iIEy7gk9nAa+p69J0uFtxqaHykFIASlSH5p2pcLGpiuZVUox9QiXVHMYeu\n/Fzi+NKoCk9CzzemwbSYX2w=\n-----END PRIVATE KEY-----\n",
                "client_email": "firebase-adminsdk-fbsvc@pos-si2.iam.gserviceaccount.com",
                "client_id": "106991051260846944103",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40pos-si2.iam.gserviceaccount.com",
                "universe_domain": "googleapis.com"
            }
            
            cred = credentials.Certificate(firebase_config)
            _app = initialize_app(cred)
            print("[FIREBASE] ¡Conexión forzada establecida con éxito!")
            return messaging
        except Exception as e:
            print(f"[FIREBASE ERROR] Error crítico en inicialización forzada: {str(e)}")
            return None
            
    return messaging