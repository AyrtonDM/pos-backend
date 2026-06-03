# -*- coding: utf-8 -*-
import os
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import JWTError
from jose import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import JWT_ALGORITHM
from app.core.security import JWT_SECRET_KEY
from app.models.usuarios import Usuario
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.rol_repository import RolRepository
from app.repositories.sucursal_repository import SucursalRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.cliente_repository import ClienteRepository
from app.services.inventario_service import InventarioService
from app.utils.email_service import (
    send_client_invitation_email,
    send_employee_invitation_email,
)

DEFAULT_APP_BASE_URL = "https://pos-backend-app.duckdns.org"


class SucursalService:
    @staticmethod
    def _crear_token_invitacion_empleado(
        id_empresa: int,
        id_usuario: int,
        id_rol: int,
        id_sucursales: list[int],
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(hours=int(os.getenv("INVITATION_EXPIRATION_HOURS", "72")))
        payload = {
            "tipo": "invitacion_empleado",
            "id_empresa": id_empresa,
            "id_usuario": id_usuario,
            "id_rol": id_rol,
            "id_sucursales": id_sucursales,
            "iat": now,
            "exp": expire,
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def _leer_token_invitacion_empleado(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as exc:
            raise ValueError("Invitacion invalida o expirada.") from exc

        if payload.get("tipo") != "invitacion_empleado":
            raise ValueError("Invitacion invalida.")

        return payload

    @staticmethod
    def _validar_usuario_activo(current_user: Usuario) -> None:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

    @staticmethod
    def _validar_empresa_del_usuario(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ) -> None:
        SucursalService._validar_usuario_activo(current_user)

        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

    @staticmethod
    def crear_sucursal_para_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        nombre: str,
        direccion: str,
        telefono: str,
        ciudad: str,
    ):
        SucursalService._validar_empresa_del_usuario(db, current_user, id_empresa)

        try:
            sucursal = SucursalRepository.crear_sucursal(
                db=db,
                datos={
                    "id_empresa": id_empresa,
                    "nombre": nombre,
                    "direccion": direccion,
                    "telefono": telefono,
                    "ciudad": ciudad,
                    "fecha_registro": date.today(),
                    "activo": True,
                },
            )

            usuario_rol_sin_sucursal = EmpresaRepository.obtener_usuario_rol_sin_sucursal(
                db=db,
                id_usuario=current_user.id_usuario,
                id_empresa=id_empresa,
            )

            if usuario_rol_sin_sucursal is not None:
                EmpresaRepository.asignar_sucursal_a_usuario_rol(
                    db=db,
                    usuario_rol=usuario_rol_sin_sucursal,
                    id_sucursal=sucursal.id_sucursal,
                )
            else:
                usuario_rol_base = EmpresaRepository.obtener_usuario_rol_activo(
                    db=db,
                    id_usuario=current_user.id_usuario,
                    id_empresa=id_empresa,
                )
                if usuario_rol_base is None:
                    raise LookupError("Empresa no encontrada para este usuario.")

                EmpresaRepository.crear_usuario_rol(
                    db=db,
                    id_usuario=current_user.id_usuario,
                    id_rol=usuario_rol_base.id_rol,
                    id_empresa=id_empresa,
                    id_sucursal=sucursal.id_sucursal,
                    activo=True,
                )

            InventarioService.sincronizar_stocks_por_sucursal(
                db=db,
                id_sucursal=sucursal.id_sucursal,
                fecha_actualizacion=datetime.now(),
            )
            db.commit()
            db.refresh(sucursal)
            return sucursal
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo asignar la sucursal al usuario.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def obtener_sucursales_de_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ):
        SucursalService._validar_empresa_del_usuario(db, current_user, id_empresa)

        return SucursalRepository.obtener_sucursales_por_empresa_y_usuario(
            db=db,
            id_empresa=id_empresa,
            id_usuario=current_user.id_usuario,
        )

    @staticmethod
    def obtener_sucursal_de_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_sucursal: int,
    ):
        SucursalService._validar_empresa_del_usuario(db, current_user, id_empresa)

        sucursal = SucursalRepository.obtener_sucursal_por_empresa(
            db=db,
            id_empresa=id_empresa,
            id_sucursal=id_sucursal,
        )
        if sucursal is None:
            raise LookupError("Sucursal no encontrada para esta empresa.")

        return sucursal

    @staticmethod
    def actualizar_sucursal_del_usuario(
        db: Session,
        current_user: Usuario,
        id_sucursal: int,
        nombre: str,
        direccion: str,
        telefono: str,
        ciudad: str,
        activo: bool,
    ):
        SucursalService._validar_usuario_activo(current_user)

        sucursal = SucursalRepository.obtener_sucursal_por_id(
            db=db,
            id_sucursal=id_sucursal,
        )
        if sucursal is None:
            raise LookupError("Sucursal no encontrada.")

        SucursalService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=sucursal.id_empresa,
        )

        return SucursalRepository.actualizar_sucursal(
            db=db,
            sucursal=sucursal,
            datos={
                "nombre": nombre,
                "direccion": direccion,
                "telefono": telefono,
                "ciudad": ciudad,
                "activo": activo,
            },
        )

    @staticmethod
    def enviar_invitacion_empleado(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        email: str,
        id_sucursales: list[int],
        id_rol: int,
    ) -> dict:
        SucursalService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )

        id_sucursales_unicas = list(dict.fromkeys(id_sucursales))
        if len(id_sucursales_unicas) != len(id_sucursales):
            raise ValueError("No se permiten sucursales repetidas en la invitacion.")

        sucursales = []
        for id_sucursal in id_sucursales_unicas:
            sucursal = SucursalRepository.obtener_sucursal_por_empresa(
                db=db,
                id_empresa=id_empresa,
                id_sucursal=id_sucursal,
            )
            if sucursal is None:
                raise LookupError("Sucursal no encontrada para esta empresa.")
            sucursales.append(sucursal)

        usuario_invitado = UsuarioRepository.obtener_usuario_por_email(db, email)
        if usuario_invitado is None:
            raise LookupError("No existe un usuario con ese correo.")

        rol = RolRepository.obtener_rol_por_id(db=db, id_rol=id_rol)
        if rol is None or not rol.activo:
            raise LookupError("Rol no encontrado o inactivo.")
        if rol.id_empresa is not None and rol.id_empresa != id_empresa:
            raise ValueError("El rol no pertenece a esta empresa.")

        base_url = os.getenv("APP_BASE_URL", DEFAULT_APP_BASE_URL).rstrip("/")
        token = SucursalService._crear_token_invitacion_empleado(
            id_empresa=id_empresa,
            id_usuario=usuario_invitado.id_usuario,
            id_rol=id_rol,
            id_sucursales=id_sucursales_unicas,
        )
        invitation_link = f"{base_url}/api/invitaciones/empleado/aceptar/{token}"
        nombre = (
            usuario_invitado.persona.nombre_completo
            if usuario_invitado.persona
            else usuario_invitado.email
        )
        email_enviado = send_employee_invitation_email(
            email=usuario_invitado.email,
            nombre=nombre,
            invitation_link=invitation_link,
        )
        if not email_enviado:
            raise ValueError("No se pudo enviar el correo de invitacion.")

        return {
            "mensaje": "Invitacion enviada correctamente.",
            "email": usuario_invitado.email,
            "link_invitacion": invitation_link,
            "id_sucursales": [sucursal.id_sucursal for sucursal in sucursales],
            "id_rol": id_rol,
        }

    @staticmethod
    def enviar_invitacion_cliente(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        email: str,
    ) -> dict:
        SucursalService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )

        empresa = EmpresaRepository.obtener_empresa_por_id(db=db, id_empresa=id_empresa)
        if empresa is None:
            raise LookupError("Empresa no encontrada.")

        usuario_invitado = UsuarioRepository.obtener_usuario_por_email(db, email)
        if usuario_invitado is None:
            raise LookupError("No existe un usuario con ese correo.")

        rol_cliente = EmpresaRepository.obtener_rol_por_nombre(
            db=db,
            nombre="CLIENTE",
        )
        if rol_cliente is None:
            raise ValueError("No existe el rol CLIENTE.")

        usuario_rol_existente = EmpresaRepository.obtener_usuario_rol_por_empresa_y_rol_sin_sucursal(
            db=db,
            id_usuario=usuario_invitado.id_usuario,
            id_empresa=id_empresa,
            id_rol=rol_cliente.id_rol,
        )
        if usuario_rol_existente is not None:
            raise ValueError("El usuario ya es cliente de esta empresa.")

        base_url = os.getenv("APP_BASE_URL", DEFAULT_APP_BASE_URL).rstrip("/")
        invitation_link = (
            f"{base_url}/api/invitaciones/cliente/aceptar/"
            f"{id_empresa}/{usuario_invitado.id_usuario}"
        )
        nombre = (
            usuario_invitado.persona.nombre_completo
            if usuario_invitado.persona
            else usuario_invitado.email
        )
        email_enviado = send_client_invitation_email(
            email=usuario_invitado.email,
            nombre=nombre,
            empresa_nombre=empresa.nombre,
            invitation_link=invitation_link,
        )
        if not email_enviado:
            raise ValueError("No se pudo enviar el correo de invitacion.")

        return {
            "mensaje": "Invitacion enviada correctamente.",
            "email": usuario_invitado.email,
            "link_invitacion": invitation_link,
        }

    @staticmethod
    def aceptar_invitacion_empleado(
        db: Session,
        token: str,
    ) -> dict:
        payload = SucursalService._leer_token_invitacion_empleado(token)

        try:
            id_empresa = int(payload["id_empresa"])
            id_usuario = int(payload["id_usuario"])
            id_rol = int(payload["id_rol"])
            id_sucursales = [int(id_sucursal) for id_sucursal in payload["id_sucursales"]]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invitacion invalida.") from exc

        if not id_sucursales:
            raise ValueError("La invitacion no contiene sucursales.")

        usuario = UsuarioRepository.obtener_usuario_por_id(db, id_usuario)
        if usuario is None or not usuario.activo:
            raise LookupError("Usuario no encontrado o inactivo.")

        empresa = EmpresaRepository.obtener_empresa_por_id(db=db, id_empresa=id_empresa)
        if empresa is None:
            raise LookupError("Empresa no encontrada.")

        rol = RolRepository.obtener_rol_por_id(db=db, id_rol=id_rol)
        if rol is None or not rol.activo:
            raise LookupError("Rol no encontrado o inactivo.")
        if rol.id_empresa is not None and rol.id_empresa != id_empresa:
            raise ValueError("El rol no pertenece a esta empresa.")

        sucursales = []
        for id_sucursal in list(dict.fromkeys(id_sucursales)):
            sucursal = SucursalRepository.obtener_sucursal_por_empresa(
                db=db,
                id_empresa=id_empresa,
                id_sucursal=id_sucursal,
            )
            if sucursal is None:
                raise LookupError("Sucursal no encontrada para esta empresa.")
            sucursales.append(sucursal)

        usuarios_rol_creados = []
        usuarios_rol_existentes = []
        try:
            for sucursal in sucursales:
                usuario_rol_existente = EmpresaRepository.obtener_usuario_rol_por_sucursal_y_rol(
                    db=db,
                    id_usuario=id_usuario,
                    id_empresa=id_empresa,
                    id_sucursal=sucursal.id_sucursal,
                    id_rol=id_rol,
                )
                if usuario_rol_existente is not None:
                    usuarios_rol_existentes.append(usuario_rol_existente)
                    continue

                usuario_rol = EmpresaRepository.crear_usuario_rol(
                    db=db,
                    id_usuario=id_usuario,
                    id_rol=id_rol,
                    id_empresa=id_empresa,
                    id_sucursal=sucursal.id_sucursal,
                    activo=True,
                )
                usuarios_rol_creados.append(usuario_rol)

            db.commit()
            for usuario_rol in [*usuarios_rol_creados, *usuarios_rol_existentes]:
                db.refresh(usuario_rol)
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo aceptar la invitacion.") from exc
        except Exception:
            db.rollback()
            raise

        return {
            "mensaje": "Invitacion aceptada correctamente.",
            "ya_aceptada": len(usuarios_rol_creados) == 0,
            "id_usuario": id_usuario,
            "id_empresa": id_empresa,
            "id_rol": id_rol,
            "empresa": empresa.nombre,
            "usuario_roles_creados": [
                {
                    "id_usuario_rol": usuario_rol.id_usuario_rol,
                    "id_usuario": usuario_rol.id_usuario,
                    "id_empresa": usuario_rol.id_empresa,
                    "id_sucursal": usuario_rol.id_sucursal,
                    "id_rol": usuario_rol.id_rol,
                }
                for usuario_rol in usuarios_rol_creados
            ],
            "usuario_roles_existentes": [
                {
                    "id_usuario_rol": usuario_rol.id_usuario_rol,
                    "id_usuario": usuario_rol.id_usuario,
                    "id_empresa": usuario_rol.id_empresa,
                    "id_sucursal": usuario_rol.id_sucursal,
                    "id_rol": usuario_rol.id_rol,
                }
                for usuario_rol in usuarios_rol_existentes
            ],
        }

    @staticmethod
    def aceptar_invitacion_cliente(
        db: Session,
        id_empresa: int,
        id_usuario: int,
    ) -> dict:
        usuario = UsuarioRepository.obtener_usuario_por_id(db, id_usuario)
        if usuario is None or not usuario.activo:
            raise LookupError("Usuario no encontrado o inactivo.")

        empresa = EmpresaRepository.obtener_empresa_por_id(db=db, id_empresa=id_empresa)
        if empresa is None:
            raise LookupError("Empresa no encontrada.")

        rol_cliente = EmpresaRepository.obtener_rol_por_nombre(
            db=db,
            nombre="CLIENTE",
        )
        if rol_cliente is None:
            raise ValueError("No existe el rol CLIENTE.")

        usuario_rol_existente = EmpresaRepository.obtener_usuario_rol_por_empresa_y_rol_sin_sucursal(
            db=db,
            id_usuario=id_usuario,
            id_empresa=id_empresa,
            id_rol=rol_cliente.id_rol,
        )
        if usuario_rol_existente is not None:
            return {
                "mensaje": f"Ya eres cliente de {empresa.nombre}.",
                "empresa_nombre": empresa.nombre,
                "id_usuario_rol": usuario_rol_existente.id_usuario_rol,
                "id_usuario": usuario_rol_existente.id_usuario,
                "id_empresa": usuario_rol_existente.id_empresa,
                "id_sucursal": usuario_rol_existente.id_sucursal,
                "id_rol": usuario_rol_existente.id_rol,
            }

        try:
            usuario_rol = EmpresaRepository.crear_usuario_rol(
                db=db,
                id_usuario=id_usuario,
                id_rol=rol_cliente.id_rol,
                id_empresa=id_empresa,
                id_sucursal=None,
                activo=True,
            )
            db.commit()
            db.refresh(usuario_rol)

            # Crear registro en la tabla cliente asociado al usuario
            try:
                cliente = ClienteRepository.crear_cliente(
                    db=db,
                    datos={
                        "id_usuario": id_usuario,
                        "id_categoria_cliente": None,
                        "codigo_cliente": "CLI-TEMP",
                        "saldo_credito": None,
                        "limite_credito": None,
                        "activo": True,
                    },
                )
                # Asignar codigo definitivo basado en id_cliente (3 dígitos)
                cliente.codigo_cliente = f"CLI-{cliente.id_cliente:03d}"
                db.commit()
                db.refresh(cliente)
            except Exception:
                db.rollback()
                # No interrumpimos la aceptación si falla la creación del cliente,
                # pero propagamos el error para que se pueda investigar.
                raise
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo aceptar la invitacion.") from exc
        except Exception:
            db.rollback()
            raise

        return {
            "mensaje": f"Ahora eres cliente de {empresa.nombre}.",
            "empresa_nombre": empresa.nombre,
            "id_usuario_rol": usuario_rol.id_usuario_rol,
            "id_usuario": usuario_rol.id_usuario,
            "id_empresa": usuario_rol.id_empresa,
            "id_sucursal": usuario_rol.id_sucursal,
            "id_rol": usuario_rol.id_rol,
        }

    @staticmethod
    def obtener_personal_de_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ):
        SucursalService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )

        usuarios_rol = EmpresaRepository.obtener_personal_por_empresa_excluyendo_roles(
            db=db,
            id_empresa=id_empresa,
            roles_excluidos=["ADMINISTRADOR", "CLIENTE"],
        )

        personal_por_usuario = {}
        for usuario_rol in usuarios_rol:
            if usuario_rol.id_usuario not in personal_por_usuario:
                personal_por_usuario[usuario_rol.id_usuario] = {
                    "id_usuario": usuario_rol.id_usuario,
                    "usuario": usuario_rol.usuario,
                    "relaciones": [],
                }

            personal_por_usuario[usuario_rol.id_usuario]["relaciones"].append(
                {
                    "id_usuario_rol": usuario_rol.id_usuario_rol,
                    "id_rol": usuario_rol.id_rol,
                    "id_empresa": usuario_rol.id_empresa,
                    "id_sucursal": usuario_rol.id_sucursal,
                    "activo": usuario_rol.activo,
                }
            )

        return list(personal_por_usuario.values())

    @staticmethod
    def editar_personal_de_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        email: str,
        id_sucursales: list[int],
        id_rol: int,
        activo: bool,
    ):
        SucursalService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )

        id_sucursales_unicas = list(dict.fromkeys(id_sucursales))
        if len(id_sucursales_unicas) != len(id_sucursales):
            raise ValueError("No se permiten sucursales repetidas.")

        sucursales_encontradas = []
        for id_sucursal in id_sucursales_unicas:
            sucursal = SucursalRepository.obtener_sucursal_por_empresa(
                db=db,
                id_empresa=id_empresa,
                id_sucursal=id_sucursal,
            )
            if sucursal is None:
                raise LookupError("Sucursal no encontrada para esta empresa.")
            sucursales_encontradas.append(sucursal)

        usuario = UsuarioRepository.obtener_usuario_por_email(db, email)
        if usuario is None:
            raise LookupError("No existe un usuario con ese correo.")

        rol = RolRepository.obtener_rol_por_id(db=db, id_rol=id_rol)
        if rol is None or not rol.activo:
            raise LookupError("Rol no encontrado o inactivo.")
        if rol.id_empresa is not None and rol.id_empresa != id_empresa:
            raise ValueError("El rol no pertenece a esta empresa.")

        usuarios_rol = EmpresaRepository.obtener_usuarios_rol_por_empresa(
            db=db,
            id_usuario=usuario.id_usuario,
            id_empresa=id_empresa,
        )
        if not usuarios_rol and not activo:
            raise LookupError("No existe relacion del usuario con esta empresa.")

        try:
            if not activo:
                for usuario_rol in usuarios_rol:
                    usuario_rol.activo = False

                db.commit()
                for usuario_rol in usuarios_rol:
                    db.refresh(usuario_rol)
                return usuarios_rol

            todas_apagadas = bool(usuarios_rol) and all(
                not usuario_rol.activo for usuario_rol in usuarios_rol
            )
            if todas_apagadas:
                for usuario_rol in usuarios_rol:
                    usuario_rol.activo = True

            existentes_por_sucursal = {}
            existentes_por_sucursal_y_rol = {}
            for usuario_rol in usuarios_rol:
                if usuario_rol.id_sucursal is None:
                    continue
                existentes_por_sucursal.setdefault(usuario_rol.id_sucursal, usuario_rol)
                existentes_por_sucursal_y_rol[
                    (usuario_rol.id_sucursal, usuario_rol.id_rol)
                ] = usuario_rol

            ids_sucursales_solicitadas = set(id_sucursales_unicas)
            relaciones_seleccionadas = set()
            relaciones_creadas = []

            for sucursal in sucursales_encontradas:
                usuario_rol = existentes_por_sucursal_y_rol.get(
                    (sucursal.id_sucursal, id_rol)
                )
                if usuario_rol is None:
                    usuario_rol = existentes_por_sucursal.get(sucursal.id_sucursal)

                if usuario_rol is None:
                    usuario_rol = EmpresaRepository.crear_usuario_rol(
                        db=db,
                        id_usuario=usuario.id_usuario,
                        id_rol=id_rol,
                        id_empresa=id_empresa,
                        id_sucursal=sucursal.id_sucursal,
                        activo=True,
                    )
                    relaciones_creadas.append(usuario_rol)
                else:
                    usuario_rol.id_rol = id_rol
                    usuario_rol.activo = True

                relaciones_seleccionadas.add(usuario_rol.id_usuario_rol)

            for usuario_rol in usuarios_rol:
                if usuario_rol.id_sucursal is None:
                    continue
                if usuario_rol.id_sucursal not in ids_sucursales_solicitadas:
                    usuario_rol.activo = False
                elif usuario_rol.id_usuario_rol not in relaciones_seleccionadas:
                    usuario_rol.activo = False

            db.commit()

            resultado = EmpresaRepository.obtener_usuarios_rol_por_empresa(
                db=db,
                id_usuario=usuario.id_usuario,
                id_empresa=id_empresa,
            )
            for usuario_rol in [*resultado, *relaciones_creadas]:
                db.refresh(usuario_rol)
            return resultado
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo editar el personal.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def obtener_clientes_de_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ):
        SucursalService._validar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )

        rol_cliente = EmpresaRepository.obtener_rol_por_nombre(
            db=db,
            nombre="CLIENTE",
        )
        if rol_cliente is None:
            raise ValueError("No existe el rol CLIENTE.")

        usuarios_rol = EmpresaRepository.obtener_usuarios_rol_por_empresa_y_rol_sin_sucursal(
            db=db,
            id_empresa=id_empresa,
            id_rol=rol_cliente.id_rol,
        )

        # Para cada usuario_rol, adjuntar el cliente (registro único de la tabla cliente) asociado al usuario
        resultado = []
        for ur in usuarios_rol:
            cliente = ClienteRepository.obtener_cliente_por_usuario(db=db, id_usuario=ur.id_usuario)
            resultado.append(
                {
                    "id_usuario_rol": ur.id_usuario_rol,
                    "id_usuario": ur.id_usuario,
                    "id_rol": ur.id_rol,
                    "id_empresa": ur.id_empresa,
                    "id_sucursal": ur.id_sucursal,
                    "activo": ur.activo,
                    "usuario": ur.usuario,
                    "cliente": cliente,
                }
            )

        return resultado

    @staticmethod
    def obtener_sucursales_asignadas_como_empleado(
        db: Session,
        current_user: Usuario,
        id_empresa: int | None = None,
    ):
        SucursalService._validar_usuario_activo(current_user)

        if id_empresa is not None:
            SucursalService._validar_empresa_del_usuario(
                db=db,
                current_user=current_user,
                id_empresa=id_empresa,
            )

        rol_empleado = EmpresaRepository.obtener_rol_por_nombre(
            db=db,
            nombre="EMPLEADO",
        )
        if rol_empleado is None:
            raise ValueError("No existe el rol EMPLEADO.")

        return EmpresaRepository.obtener_sucursales_empleado_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_rol=rol_empleado.id_rol,
            id_empresa=id_empresa,
        )
