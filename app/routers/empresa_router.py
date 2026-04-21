# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.producto_schema import (
    CategoriaProductoCreate,
    CategoriaProductoResponse,
    ProductoCreate,
    ProductoResponse,
    SubcategoriaProductoResponse,
)
from app.schemas.empresa_schema import EmpresaCreate, EmpresaResponse, EmpresaUpdate
from app.services.empresa_service import EmpresaService
from app.services.producto_service import ProductoService
from app.utils.product_image_storage import save_product_image
from fastapi import File, Form, UploadFile
from decimal import Decimal

router = APIRouter(prefix="/api/empresas", tags=["empresas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/mis-empresas", response_model=list[EmpresaResponse])
def obtener_empresas_del_usuario(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.obtener_empresas_del_usuario(
            db=db,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener las empresas.")


@router.get("/{id_empresa}", response_model=EmpresaResponse)
def obtener_empresa_del_usuario(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.obtener_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la empresa.")


@router.put("/{id_empresa}", response_model=EmpresaResponse)
def actualizar_empresa(
    id_empresa: int,
    datos: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.actualizar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            razon_social=datos.razon_social,
            nit=datos.nit,
            correo=datos.correo,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la empresa.")


@router.post("/crear", response_model=dict)
def crear_empresa(
    datos: EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.crear_empresa_para_usuario(
            db=db,
            current_user=current_user,
            nombre=datos.nombre,
            razon_social=datos.razon_social,
            nit=datos.nit,
            correo=datos.correo,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la empresa.")


@router.post("/{id_empresa}/categorias", response_model=CategoriaProductoResponse)
def crear_categoria_empresa(
    id_empresa: int,
    datos: CategoriaProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.crear_categoria(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la categoria.")


@router.get("/{id_empresa}/subcategorias", response_model=list[SubcategoriaProductoResponse])
def listar_subcategorias_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.listar_subcategorias_por_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar las subcategorias.")


@router.post("/{id_empresa}/productos", response_model=ProductoResponse)
def crear_producto_empresa(
    id_empresa: int,
    datos: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.crear_producto(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            payload=datos,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el producto.")


@router.post("/{id_empresa}/productos/con-imagen", response_model=ProductoResponse)
def crear_producto_con_imagen_empresa(
    id_empresa: int,
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
            id_empresa=id_empresa,
            payload=payload,
            imagen=imagen_path,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el producto con imagen.")
