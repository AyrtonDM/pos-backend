# -*- coding: utf-8 -*-
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi import File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios.usuario import Usuario
from app.schemas.producto_schema import (
    CategoriaProductoCreate,
    CategoriaProductoResponse,
    CategoriaProductoUpdate,
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
    SubcategoriaProductoCreate,
    SubcategoriaProductoResponse,
    SubcategoriaProductoUpdate,
)
from app.services.producto_service import ProductoService
from app.utils.product_image_storage import save_product_image

router = APIRouter(prefix="/api/productos", tags=["productos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/categorias", response_model=list[CategoriaProductoResponse])
def listar_categorias(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.listar_categorias(db=db)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar las categorias.")


@router.post("/categorias", response_model=CategoriaProductoResponse)
def crear_categoria(datos: CategoriaProductoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.crear_categoria(
            db=db,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activo=datos.activo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la categoria.")


@router.get("/categorias/{id_categoria_producto}", response_model=CategoriaProductoResponse)
def obtener_categoria(id_categoria_producto: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.obtener_categoria(db=db, id_categoria_producto=id_categoria_producto)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la categoria.")


@router.put("/categorias/{id_categoria_producto}", response_model=CategoriaProductoResponse)
def actualizar_categoria(
    id_categoria_producto: int,
    datos: CategoriaProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.actualizar_categoria(
            db=db,
            id_categoria_producto=id_categoria_producto,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la categoria.")


@router.get("/subcategorias", response_model=list[SubcategoriaProductoResponse])
def listar_subcategorias(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.listar_subcategorias(db=db)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar las subcategorias.")


@router.post("/subcategorias", response_model=SubcategoriaProductoResponse)
def crear_subcategoria(datos: SubcategoriaProductoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.crear_subcategoria(
            db=db,
            id_categoria_producto=datos.id_categoria_producto,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la subcategoria.")


@router.get("/subcategorias/{id_subcategoria}", response_model=SubcategoriaProductoResponse)
def obtener_subcategoria(id_subcategoria: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.obtener_subcategoria(db=db, id_subcategoria=id_subcategoria)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la subcategoria.")


@router.put("/subcategorias/{id_subcategoria}", response_model=SubcategoriaProductoResponse)
def actualizar_subcategoria(
    id_subcategoria: int,
    datos: SubcategoriaProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.actualizar_subcategoria(
            db=db,
            id_subcategoria=id_subcategoria,
            id_categoria_producto=datos.id_categoria_producto,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la subcategoria.")


@router.get("", response_model=list[ProductoResponse])
def listar_productos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.listar_productos(db=db, current_user=current_user)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar los productos.")


@router.post("", response_model=ProductoResponse)
def crear_producto(datos: ProductoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.crear_producto(db=db, current_user=current_user, payload=datos)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el producto.")


@router.post("/con-imagen", response_model=ProductoResponse)
def crear_producto_con_imagen(
    id_subcategoria: int = Form(...),
    nombre: str = Form(...),
    descripcion: str | None = Form(None),
    unidad_medida: str = Form(...),
    precio: Decimal = Form(Decimal("0")),
    activo: bool = Form(True),
    imagen: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        imagen_path = None
        if imagen is not None and imagen.filename:
            imagen_path = save_product_image(imagen)

        payload = ProductoCreate(
            id_subcategoria=id_subcategoria,
            nombre=nombre,
            descripcion=descripcion,
            unidad_medida=unidad_medida,
            precio=precio,
            activo=activo,
        )

        return ProductoService.crear_producto(
            db=db,
            current_user=current_user,
            payload=payload,
            imagen=imagen_path,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el producto con imagen.")


@router.get("/{id_producto}", response_model=ProductoResponse)
def obtener_producto(id_producto: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        return ProductoService.obtener_producto(db=db, current_user=current_user, id_producto=id_producto)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el producto.")


@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(
    id_producto: int,
    datos: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.actualizar_producto(db=db, current_user=current_user, id_producto=id_producto, payload=datos)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar el producto.")


@router.put("/{id_producto}/imagen", response_model=ProductoResponse)
def actualizar_imagen_producto(
    id_producto: int,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        imagen_path = save_product_image(imagen)
        return ProductoService.actualizar_imagen_producto(
            db=db,
            current_user=current_user,
            id_producto=id_producto,
            imagen=imagen_path,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la imagen del producto.")


@router.delete("/{id_producto}")
def eliminar_producto(id_producto: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    try:
        ProductoService.eliminar_producto(db=db, current_user=current_user, id_producto=id_producto)
        return {"mensaje": "Producto eliminado correctamente."}
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al eliminar el producto.")
