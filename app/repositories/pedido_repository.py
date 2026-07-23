from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.ventas.pedido_cliente import PedidoCliente
from app.models.ventas.pedido_cliente_detalle import PedidoClienteDetalle


class PedidoRepository:
    @staticmethod
    def crear_pedido(db: Session, datos: dict) -> PedidoCliente:
        pedido = PedidoCliente(**datos)
        db.add(pedido)
        return pedido

    @staticmethod
    def crear_detalle_pedido(db: Session, datos: dict) -> PedidoClienteDetalle:
        detalle = PedidoClienteDetalle(**datos)
        db.add(detalle)
        return detalle

    @staticmethod
    def obtener_pedido_por_id(db: Session, id_pedido: int) -> PedidoCliente | None:
        return db.query(PedidoCliente).filter(PedidoCliente.id_pedido == id_pedido).first()

    @staticmethod
    def obtener_pedidos_por_cliente(db: Session, id_cliente: int) -> List[PedidoCliente]:
        return (
            db.query(PedidoCliente)
            .filter(PedidoCliente.id_cliente == id_cliente)
            .order_by(PedidoCliente.fecha_creacion.desc())
            .all()
        )

    @staticmethod
    def obtener_pedidos_por_empresa(
        db: Session,
        id_empresa: int,
        id_sucursal: int | None = None,
        estado: str | None = None,
    ) -> List[PedidoCliente]:
        query = (
            db.query(PedidoCliente)
            .filter(PedidoCliente.id_empresa == id_empresa)
        )
        if id_sucursal is not None:
            query = query.filter(PedidoCliente.id_sucursal == id_sucursal)
        if estado is not None:
            query = query.filter(PedidoCliente.estado == estado)
        return query.order_by(PedidoCliente.fecha_creacion.desc()).all()

    @staticmethod
    def obtener_pedidos_por_sucursal(db: Session, id_sucursal: int) -> List[PedidoCliente]:
        return (
            db.query(PedidoCliente)
            .filter(PedidoCliente.id_sucursal == id_sucursal)
            .order_by(PedidoCliente.fecha_creacion.desc())
            .all()
        )

    @staticmethod
    def actualizar_pedido(db: Session, pedido: PedidoCliente, datos: dict) -> PedidoCliente:
        for clave, valor in datos.items():
            setattr(pedido, clave, valor)
        return pedido
