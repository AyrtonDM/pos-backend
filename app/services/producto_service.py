# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuarios.usuario import Usuario
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.producto_repository import ProductoRepository
from app.schemas.producto_schema import (
    CategoriaProductoCreate,
    CategoriaProductoResponse,
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
    StockCreate,
    StockResponse,
    StockUpdate,
    SubcategoriaProductoCreate,
    SubcategoriaProductoResponse,
    SubcategoriaProductoUpdate,
)


class ProductoService:
    @staticmethod
    def _validar_usuario_activo(current_user: Usuario) -> None:
        if current_user is None or not current_user.activo:
            raise ValueError("Usuario no autorizado o inactivo.")

    @staticmethod
    def _validar_empresa_del_usuario(db: Session, current_user: Usuario, id_empresa: int) -> None:
        ProductoService._validar_usuario_activo(current_user)

        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

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
    def _validar_stock(stock) -> None:
        if stock is None:
            return
        if stock.stock_min is not None and stock.stock_max is not None and stock.stock_min > stock.stock_max:
            raise ValueError("stock_min no puede ser mayor que stock_max.")
        if getattr(stock, "cantidad", None) is not None and stock.cantidad < 0:
            raise ValueError("La cantidad de stock no puede ser negativa.")

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
    def _serializar_stock(stock) -> dict:
        return {
            "id_stock": stock.id_stock,
            "cantidad": stock.cantidad,
            "stock_min": stock.stock_min,
            "stock_max": stock.stock_max,
            "fecha_actualizacion": stock.fecha_actualizacion,
        }

    @staticmethod
    def _serializar_producto(producto) -> dict:
        return {
            "id_producto": producto.id_producto,
            "id_empresa": producto.id_empresa,
            "id_subcategoria": producto.id_subcategoria,
            "nombre": producto.nombre,
            "costo": producto.costo,
            "precio": producto.precio,
            "imagen": producto.imagen,
            "subcategoria": ProductoService._serializar_subcategoria(producto.subcategoria),
            "stock": ProductoService._serializar_stock(producto.stock),
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
    def eliminar_categoria(db: Session, id_categoria_producto: int) -> None:
        categoria = ProductoRepository.obtener_categoria_por_id(db, id_categoria_producto)
        if categoria is None:
            raise LookupError("Categoria no encontrada.")
        ProductoRepository.eliminar_categoria(categoria, db)

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
    def eliminar_subcategoria(db: Session, id_subcategoria: int) -> None:
        subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, id_subcategoria)
        if subcategoria is None:
            raise LookupError("Subcategoria no encontrada.")
        ProductoRepository.eliminar_subcategoria(subcategoria, db)

    @staticmethod
    def listar_productos(db: Session, current_user: Usuario, id_empresa: int | None = None):
        ProductoService._validar_usuario_activo(current_user)

        if id_empresa is not None:
            ProductoService._validar_empresa_del_usuario(db, current_user, id_empresa)
            productos = ProductoRepository.obtener_productos_por_empresa(db, id_empresa)
        else:
            empresas = EmpresaRepository.obtener_empresas_por_usuario(db, current_user.id_usuario)
            if not empresas:
                return []
            productos = []
            for empresa in empresas:
                productos.extend(ProductoRepository.obtener_productos_por_empresa(db, empresa.id_empresa))

        return [ProductoResponse.model_validate(ProductoService._serializar_producto(producto)) for producto in productos]

    @staticmethod
    def crear_producto(
        db: Session,
        current_user: Usuario,
        payload: ProductoCreate,
        imagen: str | None = None,
    ) -> ProductoResponse:
        ProductoService._validar_empresa_del_usuario(db, current_user, payload.id_empresa)

        subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, payload.id_subcategoria)
        ProductoService._validar_subcategoria_activa(subcategoria)

        ProductoService._validar_stock(payload.stock)

        try:
            producto = ProductoRepository.crear_producto(
                db=db,
                datos={
                    "id_empresa": payload.id_empresa,
                    "id_subcategoria": payload.id_subcategoria,
                    "nombre": payload.nombre,
                    "costo": payload.costo,
                    "precio": payload.precio,
                    "imagen": imagen,
                },
            )
            ProductoRepository.crear_stock(
                db=db,
                datos={
                    "id_producto": producto.id_producto,
                    "cantidad": payload.stock.cantidad,
                    "stock_min": payload.stock.stock_min,
                    "stock_max": payload.stock.stock_max,
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
        ProductoService._validar_empresa_del_usuario(db, current_user, producto.id_empresa)
        return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))

    @staticmethod
    def actualizar_producto(db: Session, current_user: Usuario, id_producto: int, payload: ProductoUpdate) -> ProductoResponse:
        ProductoService._validar_usuario_activo(current_user)
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        ProductoService._validar_empresa_del_usuario(db, current_user, producto.id_empresa)

        datos = {}
        if payload.id_empresa is not None and payload.id_empresa != producto.id_empresa:
            ProductoService._validar_empresa_del_usuario(db, current_user, payload.id_empresa)
            datos["id_empresa"] = payload.id_empresa
        if payload.id_subcategoria is not None:
            subcategoria = ProductoRepository.obtener_subcategoria_por_id(db, payload.id_subcategoria)
            ProductoService._validar_subcategoria_activa(subcategoria)
            datos["id_subcategoria"] = payload.id_subcategoria
        if payload.nombre is not None:
            datos["nombre"] = payload.nombre
        if payload.costo is not None:
            datos["costo"] = payload.costo
        if payload.precio is not None:
            datos["precio"] = payload.precio

        if payload.stock is not None:
            ProductoService._validar_stock(payload.stock)

        try:
            if datos:
                producto = ProductoRepository.actualizar_producto(producto, datos, db)

            if payload.stock is not None:
                stock = ProductoRepository.obtener_stock_por_producto(db, producto.id_producto)
                if stock is None:
                    ProductoRepository.crear_stock(
                        db=db,
                        datos={
                            "id_producto": producto.id_producto,
                            "cantidad": payload.stock.cantidad or 0,
                            "stock_min": payload.stock.stock_min or 0,
                            "stock_max": payload.stock.stock_max or 0,
                        },
                    )
                else:
                    stock_datos = {}
                    if payload.stock.cantidad is not None:
                        stock_datos["cantidad"] = payload.stock.cantidad
                    if payload.stock.stock_min is not None:
                        stock_datos["stock_min"] = payload.stock.stock_min
                    if payload.stock.stock_max is not None:
                        stock_datos["stock_max"] = payload.stock.stock_max
                    ProductoRepository.actualizar_stock(stock, stock_datos, db)

            db.commit()
            producto = ProductoRepository.obtener_producto_por_id(db, producto.id_producto)
            return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo actualizar el producto.") from exc

    @staticmethod
    def eliminar_producto(db: Session, current_user: Usuario, id_producto: int) -> None:
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        ProductoService._validar_empresa_del_usuario(db, current_user, producto.id_empresa)
        ProductoRepository.eliminar_producto(producto, db)

    @staticmethod
    def obtener_stock_de_producto(db: Session, current_user: Usuario, id_producto: int) -> StockResponse:
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        ProductoService._validar_empresa_del_usuario(db, current_user, producto.id_empresa)
        stock = ProductoRepository.obtener_stock_por_producto(db, id_producto)
        if stock is None:
            raise LookupError("Stock no encontrado.")
        return StockResponse.model_validate(ProductoService._serializar_stock(stock))

    @staticmethod
    def actualizar_stock_de_producto(
        db: Session,
        current_user: Usuario,
        id_producto: int,
        payload: StockUpdate,
    ) -> StockResponse:
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        ProductoService._validar_empresa_del_usuario(db, current_user, producto.id_empresa)
        ProductoService._validar_stock(payload)

        stock = ProductoRepository.obtener_stock_por_producto(db, id_producto)
        if stock is None:
            stock = ProductoRepository.crear_stock(
                db=db,
                datos={
                    "id_producto": id_producto,
                    "cantidad": payload.cantidad or 0,
                    "stock_min": payload.stock_min or 0,
                    "stock_max": payload.stock_max or 0,
                },
            )
            db.commit()
            return StockResponse.model_validate(ProductoService._serializar_stock(stock))

        datos = {}
        if payload.cantidad is not None:
            datos["cantidad"] = payload.cantidad
        if payload.stock_min is not None:
            datos["stock_min"] = payload.stock_min
        if payload.stock_max is not None:
            datos["stock_max"] = payload.stock_max

        stock = ProductoRepository.actualizar_stock(stock, datos, db)
        return StockResponse.model_validate(ProductoService._serializar_stock(stock))

    @staticmethod
    def actualizar_imagen_producto(
        db: Session,
        current_user: Usuario,
        id_producto: int,
        imagen: str,
    ) -> ProductoResponse:
        producto = ProductoRepository.obtener_producto_por_id(db, id_producto)
        if producto is None:
            raise LookupError("Producto no encontrado.")

        ProductoService._validar_empresa_del_usuario(db, current_user, producto.id_empresa)

        producto = ProductoRepository.actualizar_producto(producto, {"imagen": imagen}, db)
        return ProductoResponse.model_validate(ProductoService._serializar_producto(producto))