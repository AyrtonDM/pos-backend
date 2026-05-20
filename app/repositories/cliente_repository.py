# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.clientes.categoria_cliente import CategoriaCliente
from app.models.clientes.cliente import Cliente


class ClienteRepository:
    @staticmethod
    def crear_categoria_cliente(db: Session, datos: dict) -> CategoriaCliente:
        categoria = CategoriaCliente(**datos)
        db.add(categoria)
        db.commit()
        db.refresh(categoria)
        return categoria

    @staticmethod
    def obtener_categoria_cliente_por_id(
        db: Session, id_categoria_cliente: int
    ) -> CategoriaCliente | None:
        return db.query(CategoriaCliente).filter(
            CategoriaCliente.id_categoria_cliente == id_categoria_cliente
        ).first()

    @staticmethod
    def obtener_categorias_cliente_por_empresa(
        db: Session, id_empresa: int
    ) -> list[CategoriaCliente]:
        return db.query(CategoriaCliente).filter(
            CategoriaCliente.id_empresa == id_empresa
        ).all()

    @staticmethod
    def obtener_todas_categorias_cliente(db: Session) -> list[CategoriaCliente]:
        return db.query(CategoriaCliente).all()

    @staticmethod
    def actualizar_categoria_cliente(
        db: Session, categoria: CategoriaCliente, datos: dict
    ) -> CategoriaCliente:
        for key, value in datos.items():
            if value is not None:
                setattr(categoria, key, value)
        db.commit()
        db.refresh(categoria)
        return categoria

    @staticmethod
    def eliminar_categoria_cliente(db: Session, id_categoria_cliente: int) -> bool:
        categoria = ClienteRepository.obtener_categoria_cliente_por_id(db, id_categoria_cliente)
        if categoria:
            db.delete(categoria)
            db.commit()
            return True
        return False

    @staticmethod
    def crear_cliente(db: Session, datos: dict) -> Cliente:
        cliente = Cliente(**datos)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente

    @staticmethod
    def obtener_cliente_por_id(db: Session, id_cliente: int) -> Cliente | None:
        return db.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()

    @staticmethod
    def obtener_clientes_por_empresa(db: Session, id_empresa: int) -> list[Cliente]:
        return db.query(Cliente).filter(Cliente.id_empresa == id_empresa).all()

    @staticmethod
    def obtener_clientes_por_categoria(
        db: Session, id_categoria_cliente: int
    ) -> list[Cliente]:
        return db.query(Cliente).filter(
            Cliente.id_categoria_cliente == id_categoria_cliente
        ).all()

    @staticmethod
    def actualizar_cliente(db: Session, cliente: Cliente, datos: dict) -> Cliente:
        for key, value in datos.items():
            if value is not None:
                setattr(cliente, key, value)
        db.commit()
        db.refresh(cliente)
        return cliente
