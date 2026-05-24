"""Lista usuarios con rol 'administrador' y genera un JWT de prueba para cada uno.
Imprime email, roles, token y payload decodificado.
"""
from app.core.database import SessionLocal
from app.models.usuarios.usuario import Usuario
from app.core.security import create_access_token, JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt


def main():
    db = SessionLocal()
    try:
        usuarios = db.query(Usuario).all()
        found = False
        for u in usuarios:
            roles = []
            try:
                for ur in getattr(u, 'usuario_roles') or []:
                    r = getattr(ur, 'rol', None)
                    if r and getattr(r, 'nombre', None):
                        roles.append(r.nombre)
            except Exception:
                roles = []

            # check admin
            if any('admin' in (r or '').lower() for r in roles):
                found = True
                token = create_access_token(user_id=u.id_usuario, email=u.email, roles=roles)
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                except Exception as e:
                    payload = f"decode-error: {e}"

                print('---')
                print('email:', u.email)
                print('id:', u.id_usuario)
                print('roles:', roles)
                print('token:', token)
                print('payload:', payload)

        if not found:
            print('No se encontraron usuarios con rol administrador en la BD.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
