import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.repositories.usuario_repository import UsuarioRepository

def main():
    db = SessionLocal()
    try:
        usuario = UsuarioRepository.obtener_usuario_por_email(db, "caheba6350@diarshop.com")
        if usuario:
            usuario.activo = True
            db.commit()
            print(f"Usuario {usuario.email} activado correctamente.")
        else:
            print("Usuario no encontrado.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
