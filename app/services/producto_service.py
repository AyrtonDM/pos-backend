# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuarios.usuario import Usuario
from app.repositories.producto_repository import ProductoRepository
from app.schemas.producto_schema import (
    CategoriaProductoResponse,
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
    SubcategoriaProductoResponse,
)


class ProductoService:
    @staticmethod
    def _validar_usuario_activo(current_user: Usuario) -> None:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

    @staticmethod
    def _validar_categoria_activa(categoria) -> None:
        if categoria is None:
            raise LookupError("Categoria no encontrada.")
        if not categoria.activo:
            raise ValueError("La categoria esta inactiva.")

    @staticmethod
    def _validar_subcategoria_activa(subcategoria) -> None:
        if subcategoria is None:
            raise LookupError("Subcategoria no encontrada.")
        if not subcategoria.activo:
            raise ValueError("La subcategoria esta inactiva.")

    @staticmethod
    def _serializar_categoria(categoria) -> dict:
        return {
            "id_categoria_producto": categoria.id_categoria_producto,
            "nombre": categoria.nombre,
            "descripcion": categoria.descripcion,
            "activo": categoria.activo,
        }

    @staticmethod
    def _serializar_subcategoria(subcategoria) -> dict:
        return {
            "id_subcategoria": subcategoria.id_subcategoria,
            "id_categoria_producto": subcategoria.id_categoria_producto,
            "nombre": subcategoria.nombre,
            "descripcion": subcategoria.descripcion,
            "activo": subcategoria.activo,
        }

    @staticmethod
    def _serializar_producto(producto) -> dict:
        return {
            "id_producto": producto.id_producto,
            "id_subcategoria": producto.id_subcategoria,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "unidad_medida": producto.unidad_medida or "",
            "precio": producto.precio,
            "imagen": producto.imagen,
            "activo": producto.activo,
            "subcategoria": (
                ProductoService._serializar_subcategoria(producto.subcategoria)
                if producto.subcategoria is not None
                else None
            ),
        }

    @staticmethod
    def listar_categorias(db: Session):
        categorias = ProductoRepository.obtener_categorias(db)
        return [CategoriaProductoResponse.model_validate(ProductoService._serializar_categoria(categoria)) for categoria in categorias]

    @staticmethod
    def crear_categoria(db: Session, nombre: str, descripcion: str | None, activo: bool) -> CategoriaProductoResponse:
        try:
            categoria = ProductoRepository.crear_categoria(
                db=db,
                datos={"nombre": nombre, "descripcion": descripcion, "activo": activo},
            )
            db.commit()
            db.refresh(categoria)
            return CategoriaProductoResponse.model_validate(ProductoService._serializar_categoria(categoria))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Ya existe una categoria con ese nombre.") from exc

    @staticmethod
    def obtener_categoria(db: Session, id_categoria_producto: int) -> CategoriaProductoResponse:
        categoria = ProductoRepository.obtener_categoria_por_id(db, id_categoria_producto)
        if categoria is None:
            raise LookupError("Categoria no encontrada.")
        return CategoriaProductoResponse.model_validate(ProductoService._serializar_categoria(categoria))

    @staticmethod
    def actualizar_categoria(
        db: Session,
        id_categoria_producto: int,
        nombre: str | None,
        descripcion: str | None,
        activo: bool | None,
    ) -> CategoriaProductoResponse:
        categoria = ProductoRepository.obtener_categoria_por_id(db, id_categoria_producto)
        if categoria is None:
            raise LookupError("Categoria no encontrada.")

        datos = {}
        if nombre is not None:
            datos["nombre"] = nombre
        if descripcion is not None:
            datos["descripcion"] = descripcion
        if activo is not None:
            datos["activo"] = activo

        try:
            categoria = ProductoRepository.actualizar_categoria(categoria, datos, db)
            return CategoriaProductoResponse.model_validate(ProductoService._serializar_categoria(categoria))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Ya existe una categoria con ese nombre.") from exc

    @staticmethod
    def listar_subcategorias(db: Session):
        subcategorias = ProductoRepository.obtener_subcategorias(db)
        return [SubcategoriaProductoResponse.model_validate(ProductoService._serializar_subcategoria(subcategoria)) for subcategoria in subcategorias]

    @staticmethod
    def crear_subcategoria(
        db: Session,
        id_categoria_producto: int,
        nombre: str,
        descripcion: str | None,
        activo: bool,
    ) -> SubcategoriaProductoResponse:
        categoria = ProductoRepository.obtener_categoria_por_id(db, id_categoria_producto)
        ProductoService._validar_categoria_activa(categoria)

        try:
            subcategoria = ProductoRepository.crear_subcategoria(
                db=db,
                datos={
                    "id_categoria_producto": id_categoria_producto,
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "activo": activo,
                },
            )
            db.commit()
            db.refresh(subcategoria)
            return SubcategoriaProductoResponse.model_validate(ProductoService._serializar_subcategoria(subcategoria))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo crear la subcategoria.") from exc

    @staticmethod
    def obtener_subcategoria(db: Session, id_subcategoria: int) -> SubcategoriaProductoResponse:
        subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, id_subcategoria)
        if subcategoria is None:
            raise LookupError("Subcategoria no encontrada.")
        return SubcategoriaProductoResponse.model_validate(ProductoService._serializar_subcategoria(subcategoria))

    @staticmethod
    def actualizar_subcategoria(
        db: Session,
        id_subcategoria: int,
        id_categoria_producto: int | None,
        nombre: str | None,
        descripcion: str | None,
        activo: bool | None,
    ) -> SubcategoriaProductoResponse:
        subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, id_subcategoria)
        if subcategoria is None:
            raise LookupError("Subcategoria no encontrada.")

        datos = {}
        if id_categoria_producto is not None:
            categoria = ProductoRepository.obtener_categoria_por_id(db, id_categoria_producto)
            ProductoService._validar_categoria_activa(categoria)
            datos["id_categoria_producto"] = id_categoria_producto
        if nombre is not None:
            datos["nombre"] = nombre
        if descripcion is not None:
            datos["descripcion"] = descripcion
        if activo is not None:
            datos["activo"] = activo

        try:
            subcategoria = ProductoRepository.actualizar_subcategoria(subcategoria, datos, db)
            return SubcategoriaProductoResponse.model_validate(ProductoService._serializar_subcategoria(subcategoria))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar la subcategoria.") from exc

    @staticmethod
    def listar_productos(db: Session, current_user: Usuario):
        ProductoService._validar_usuario_activo(current_user)
        productos = ProductoRepository.obtener_productos(db)
        return [ProductoResponse.model_validate(ProductoService._serializar_producto(producto)) for producto in productos]

    @staticmethod
    def crear_producto(
        db: Session,
        current_user: Usuario,
        payload: ProductoCreate,
        imagen: str | None = None,
    ) -> ProductoResponse:
        ProductoService._validar_usuario_activo(current_user)

        subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, payload.id_subcategoria)
        ProductoService._validar_subcategoria_activa(subcategoria)

        try:
            producto = ProductoRepository.crear_producto(
                db=db,
                datos={
                    "id_subcategoria": payload.id_subcategoria,
                    "nombre": payload.nombre,
                    "descripcion": payload.descripcion,
                    "unidad_medida": payload.unidad_medida,
                    "precio": payload.precio,
                    "imagen": imagen,
                    "activo": True,
                },
            )
            db.commit()
            producto = ProductoRepository.obtener_producto_por_id(db, producto.id_producto)
            return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo crear el producto.") from exc

    @staticmethod
    def obtener_producto(db: Session, current_user: Usuario, id_producto: int) -> ProductoResponse:
        ProductoService._validar_usuario_activo(current_user)
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")
        return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))

    @staticmethod
    def actualizar_producto(db: Session, current_user: Usuario, id_producto: int, payload: ProductoUpdate) -> ProductoResponse:
        ProductoService._validar_usuario_activo(current_user)
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        datos = {}
        if payload.id_subcategoria is not None:
            subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, payload.id_subcategoria)
            ProductoService._validar_subcategoria_activa(subcategoria)
            datos["id_subcategoria"] = payload.id_subcategoria
        if payload.nombre is not None:
            datos["nombre"] = payload.nombre
        if payload.descripcion is not None:
            datos["descripcion"] = payload.descripcion
        if payload.unidad_medida is not None:
            datos["unidad_medida"] = payload.unidad_medida
        if payload.precio is not None:
            datos["precio"] = payload.precio
        if payload.activo is not None:
            datos["activo"] = payload.activo

        try:
            if datos:
                producto = ProductoRepository.actualizar_producto(producto, datos, db)
            else:
                db.refresh(producto)

            return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar el producto.") from exc

    @staticmethod
    def eliminar_producto(db: Session, current_user: Usuario, id_producto: int) -> None:
        ProductoService._validar_usuario_activo(current_user)
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")
        ProductoRepository.eliminar_producto(producto, db)

    @staticmethod
    def actualizar_imagen_producto(
        db: Session,
        current_user: Usuario,
        id_producto: int,
        imagen: str,
    ) -> ProductoResponse:
        ProductoService._validar_usuario_activo(current_user)
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        producto = ProductoRepository.actualizar_producto(producto, {"imagen": imagen}, db)
        return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))
