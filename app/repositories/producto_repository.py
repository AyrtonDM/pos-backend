# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session, joinedload

from app.models.productos import CategoriaProducto, Producto, SubcategoriaProducto


class ProductoRepository:
    @staticmethod
    def crear_categoria(db: Session, datos: dict) -> CategoriaProducto:
        categoria = CategoriaProducto(**datos)
        db.add(categoria)
        db.flush()
        db.refresh(categoria)
        return categoria

    @staticmethod
    def obtener_categoria_por_id(db: Session, id_categoria_producto: int) -> CategoriaProducto | None:
        return db.query(CategoriaProducto).filter(CategoriaProducto.id_categoria_producto == id_categoria_producto).first()

    @staticmethod
    def obtener_categorias(db: Session) -> list[CategoriaProducto]:
        return db.query(CategoriaProducto).order_by(CategoriaProducto.nombre.asc()).all()

    @staticmethod
    def actualizar_categoria(categoria: CategoriaProducto, datos: dict, db: Session) -> CategoriaProducto:
        for campo, valor in datos.items():
            setattr(categoria, campo, valor)
        db.commit()
        db.refresh(categoria)
        return categoria

    @staticmethod
    def crear_subcategoria(db: Session, datos: dict) -> SubcategoriaProducto:
        subcategoria = SubcategoriaProducto(**datos)
        db.add(subcategoria)
        db.flush()
        db.refresh(subcategoria)
        return subcategoria

    @staticmethod
    def obtener_subcategoria_por_id(db: Session, id_subcategoria: int) -> SubcategoriaProducto | None:
        return db.query(SubcategoriaProducto).filter(SubcategoriaProducto.id_subcategoria == id_subcategoria).first()

    @staticmethod
    def obtener_subcategorias(db: Session) -> list[SubcategoriaProducto]:
        return (
            db.query(SubcategoriaProducto)
            .options(joinedload(SubcategoriaProducto.categoria_producto))
            .order_by(SubcategoriaProducto.nombre.asc())
            .all()
        )

    @staticmethod
    def actualizar_subcategoria(subcategoria: SubcategoriaProducto, datos: dict, db: Session) -> SubcategoriaProducto:
        for campo, valor in datos.items():
            setattr(subcategoria, campo, valor)
        db.commit()
        db.refresh(subcategoria)
        return subcategoria

    @staticmethod
    def crear_producto(db: Session, datos: dict) -> Producto:
        producto = Producto(**datos)
        db.add(producto)
        db.flush()
        db.refresh(producto)
        return producto

    @staticmethod
    def obtener_producto_por_id(db: Session, id_producto: int) -> Producto | None:
        return (
            db.query(Producto)
            .options(joinedload(Producto.subcategoria).joinedload(SubcategoriaProducto.categoria_producto))
            .filter(Producto.id_producto == id_producto)
            .first()
        )

    @staticmethod
    def obtener_productos(db: Session) -> list[Producto]:
        return (
            db.query(Producto)
            .options(joinedload(Producto.subcategoria).joinedload(SubcategoriaProducto.categoria_producto))
            .order_by(Producto.nombre.asc())
            .all()
        )

    @staticmethod
    def actualizar_producto(producto: Producto, datos: dict, db: Session) -> Producto:
        for campo, valor in datos.items():
            setattr(producto, campo, valor)
        db.commit()
        db.refresh(producto)
        return producto

    @staticmethod
    def eliminar_producto(producto: Producto, db: Session) -> None:
        db.delete(producto)
        db.commit()
