import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.services.sucursal_service import SucursalService

def main():
    db = SessionLocal()
    try:
        # 1. Eliminar a cinthiacarrasco321@gmail.com como cliente de la empresa 2
        admin = UsuarioRepository.obtener_usuario_por_email(db, "cinthiacarrasco321@gmail.com")
        if admin:
            rol_cliente = EmpresaRepository.obtener_rol_por_nombre(db, "CLIENTE")
            if rol_cliente:
                usuario_rol = EmpresaRepository.obtener_usuario_rol_por_empresa_y_rol_sin_sucursal(
                    db=db,
                    id_usuario=admin.id_usuario,
                    id_empresa=2,
                    id_rol=rol_cliente.id_rol
                )
                if usuario_rol:
                    db.delete(usuario_rol)
                    db.commit()
                    print("Se removio a cinthiacarrasco321@gmail.com de los clientes.")

        # 2. Agregar a caheba6350@diarshop.com como cliente de la empresa 2
        email_cliente_real = "caheba6350@diarshop.com"
        cliente_real = UsuarioRepository.obtener_usuario_por_email(db, email_cliente_real)
        if not cliente_real:
            print(f"Usuario {email_cliente_real} no encontrado en la base de datos.")
            return
            
        print(f"Cliente encontrado con ID: {cliente_real.id_usuario}")
        
        # Llama a la funcion que acepta la invitacion
        resultado = SucursalService.aceptar_invitacion_cliente(
            db=db,
            id_empresa=2,
            id_usuario=cliente_real.id_usuario
        )
        print(f"Exito agregando al cliente real! Resultado: {resultado}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
