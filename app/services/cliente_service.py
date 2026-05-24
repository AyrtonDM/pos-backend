# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuarios.usuario import Usuario
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.empresa_repository import EmpresaRepository


class ClienteService:
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
        ClienteService._validar_usuario_activo(current_user)

        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

    @staticmethod
    def crear_categoria_cliente(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        nombre: str,
        descripcion: str | None,
        permite_credito: bool,
        descuento_base: float,
        limite_credito: float,
    ):
        ClienteService._validar_empresa_del_usuario(db, current_user, id_empresa)

        try:
            categoria = ClienteRepository.crear_categoria_cliente(
                db=db,
                datos={
                    "id_empresa": id_empresa,
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "permite_credito": permite_credito,
                    "descuento_base": descuento_base,
                    "limite_credito": limite_credito,
                    "activo": True,
                },
            )
            return categoria
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo crear la categoria de cliente.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def listar_categorias_cliente(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
    ):
        ClienteService._validar_empresa_del_usuario(db, current_user, id_empresa)

        return ClienteRepository.obtener_categorias_cliente_por_empresa(
            db=db,
            id_empresa=id_empresa,
        )

    @staticmethod
    def obtener_categoria_cliente(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_categoria_cliente: int,
    ):
        ClienteService._validar_empresa_del_usuario(db, current_user, id_empresa)

        categoria = ClienteRepository.obtener_categoria_cliente_por_id(
            db=db,
            id_categoria_cliente=id_categoria_cliente,
        )
        if categoria is None:
            raise LookupError("Categoria de cliente no encontrada.")

        if categoria.id_empresa != id_empresa:
            raise ValueError("Categoria de cliente no pertenece a esta empresa.")

        return categoria

    @staticmethod
    def actualizar_categoria_cliente(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_categoria_cliente: int,
        nombre: str | None,
        descripcion: str | None,
        permite_credito: bool | None,
        descuento_base: float | None,
        limite_credito: float | None,
        activo: bool | None,
    ):
        categoria = ClienteService.obtener_categoria_cliente(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_categoria_cliente=id_categoria_cliente,
        )

        try:
            return ClienteRepository.actualizar_categoria_cliente(
                db=db,
                categoria=categoria,
                datos={
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "permite_credito": permite_credito,
                    "descuento_base": descuento_base,
                    "limite_credito": limite_credito,
                    "activo": activo,
                },
            )
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar la categoria de cliente.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def crear_cliente(
        db: Session,
        current_user: Usuario,
        id_usuario: int,
        id_categoria_cliente: int,
        codigo_cliente: str,
        saldo_credito: float,
        limite_credito: float,
    ):
        ClienteService._validar_usuario_activo(current_user)

        categoria = ClienteRepository.obtener_categoria_cliente_por_id(
            db=db,
            id_categoria_cliente=id_categoria_cliente,
        )
        if categoria is None:
            raise LookupError("Categoria de cliente no encontrada.")

        try:
            cliente = ClienteRepository.crear_cliente(
                db=db,
                datos={
                    "id_usuario": id_usuario,
                    "id_categoria_cliente": id_categoria_cliente,
                    "codigo_cliente": codigo_cliente,
                    "saldo_credito": saldo_credito,
                    "limite_credito": limite_credito,
                    "activo": True,
                },
            )
            return cliente
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo crear el cliente.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def listar_clientes(
        db: Session,
        current_user: Usuario,
        id_usuario: int,
    ):
        ClienteService._validar_usuario_activo(current_user)

        return ClienteRepository.obtener_clientes_por_usuario(
            db=db,
            id_usuario=id_usuario,
        )

    @staticmethod
    def obtener_cliente(
        db: Session,
        current_user: Usuario,
        id_usuario: int,
        id_cliente: int,
    ):
        cliente = ClienteRepository.obtener_cliente_por_id(
            db=db,
            id_cliente=id_cliente,
        )
        if cliente is None:
            raise LookupError("Cliente no encontrado.")

        ClienteService._validar_usuario_activo(current_user)

        if cliente.id_usuario != id_usuario:
            raise ValueError("Cliente no pertenece a este usuario.")

        return cliente

    @staticmethod
    def actualizar_cliente(
        db: Session,
        current_user: Usuario,
        id_usuario: int,
        id_cliente: int,
        id_categoria_cliente: int | None,
        codigo_cliente: str | None,
        saldo_credito: float | None,
        limite_credito: float | None,
        activo: bool | None,
    ):
        cliente = ClienteService.obtener_cliente(
            db=db,
            current_user=current_user,
            id_usuario=id_usuario,
            id_cliente=id_cliente,
        )

        if id_categoria_cliente is not None:
            categoria = ClienteRepository.obtener_categoria_cliente_por_id(
                db=db,
                id_categoria_cliente=id_categoria_cliente,
            )
            if categoria is None:
                raise LookupError("Categoria de cliente no encontrada.")
            

        try:
            return ClienteRepository.actualizar_cliente(
                db=db,
                cliente=cliente,
                datos={
                    "id_categoria_cliente": id_categoria_cliente,
                    "codigo_cliente": codigo_cliente,
                    "saldo_credito": saldo_credito,
                    "limite_credito": limite_credito,
                    "activo": activo,
                },
            )
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar el cliente.") from exc
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def actualizar_cliente_de_empresa(
        db: Session,
        current_user: Usuario,
        id_empresa: int,
        id_cliente: int,
        id_categoria_cliente: int | None,
        codigo_cliente: str | None,
        saldo_credito: float | None,
        limite_credito: float | None,
        activo: bool | None,
    ):
        ClienteService._validar_empresa_del_usuario(db, current_user, id_empresa)

        cliente = ClienteRepository.obtener_cliente_por_id(
            db=db,
            id_cliente=id_cliente,
        )
        if cliente is None:
            raise LookupError("Cliente no encontrado.")

        empresa_del_cliente = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=cliente.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa_del_cliente is None:
            raise LookupError("Cliente no encontrado para esta empresa.")

        if id_categoria_cliente is not None:
            categoria = ClienteRepository.obtener_categoria_cliente_por_id(
                db=db,
                id_categoria_cliente=id_categoria_cliente,
            )
            if categoria is None:
                raise LookupError("Categoria de cliente no encontrada.")
            if categoria.id_empresa != id_empresa:
                raise ValueError("Categoria de cliente no pertenece a esta empresa.")

        try:
            return ClienteRepository.actualizar_cliente(
                db=db,
                cliente=cliente,
                datos={
                    "id_categoria_cliente": id_categoria_cliente,
                    "codigo_cliente": codigo_cliente,
                    "saldo_credito": saldo_credito,
                    "limite_credito": limite_credito,
                    "activo": activo,
                },
            )
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar el cliente.") from exc
        except Exception:
            db.rollback()
            raise
