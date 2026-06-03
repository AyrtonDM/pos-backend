# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios import Usuario
from app.schemas.producto_schema import (
    CategoriaProductoCreate,
    CategoriaProductoConSubcategoriasResponse,
    CategoriaProductoResponse,
    ProductoCreate,
    ProductoResponse,
    SubcategoriaProductoResponse,
)
from app.schemas.cliente_schema import (
    CategoriaClienteResponse,
    CategoriaClienteUpdate,
    ClienteResponse,
    ClienteUpdate,
)
from app.schemas.empresa_schema import EmpresaCreate, EmpresaResponse, EmpresaUpdate
from app.services.cliente_service import ClienteService
from app.services.empresa_service import EmpresaService
from app.services.producto_service import ProductoService
from app.utils.product_image_storage import save_product_image
from app.services.bitacora_service import registrar_accion
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


@router.get("/mis-empresas-empleado", response_model=list[EmpresaResponse])
def obtener_empresas_del_usuario_como_empleado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return EmpresaService.obtener_empresas_del_usuario_como_empleado(
            db=db,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al obtener las empresas del empleado.",
        )


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
        resultado = EmpresaService.actualizar_empresa_del_usuario(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            razon_social=datos.razon_social,
            nit=datos.nit,
            correo=datos.correo,
            activo=datos.activo,
        )
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            registrar_accion(
                usuario_nombre=usuario_nombre,
                accion=f"Editó la empresa ID: {id_empresa}"
            )
        except Exception:
            pass
        return resultado
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
        resultado = EmpresaService.crear_empresa_para_usuario(
            db=db,
            current_user=current_user,
            nombre=datos.nombre,
            razon_social=datos.razon_social,
            nit=datos.nit,
            correo=datos.correo,
        )
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            registrar_accion(
                usuario_nombre=usuario_nombre,
                accion=f"Registró la empresa: {datos.nombre}"
            )
        except Exception:
            pass
        return resultado
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


@router.get("/{id_empresa}/categorias-cliente", response_model=list[CategoriaClienteResponse])
def listar_categorias_cliente_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.listar_categorias_cliente(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar las categorias de cliente.")


@router.put("/{id_empresa}/categorias-cliente/{id_categoria_cliente}", response_model=CategoriaClienteResponse)
def actualizar_categoria_cliente_empresa(
    id_empresa: int,
    id_categoria_cliente: int,
    datos: CategoriaClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.actualizar_categoria_cliente(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_categoria_cliente=id_categoria_cliente,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            permite_credito=datos.permite_credito,
            descuento_base=datos.descuento_base,
            limite_credito=datos.limite_credito,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar la categoria de cliente.")


@router.put("/{id_empresa}/clientes/{id_cliente}", response_model=ClienteResponse)
def actualizar_cliente_empresa(
    id_empresa: int,
    id_cliente: int,
    datos: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.actualizar_cliente_de_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_cliente=id_cliente,
            id_categoria_cliente=datos.id_categoria_cliente,
            codigo_cliente=datos.codigo_cliente,
            saldo_credito=datos.saldo_credito,
            limite_credito=datos.limite_credito,
            activo=datos.activo,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar el cliente.")


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


@router.get("/{id_empresa}/productos", response_model=list[ProductoResponse])
def listar_productos_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.listar_productos_por_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar los productos de la empresa.")


@router.get(
    "/{id_empresa}/categorias-con-subcategorias",
    response_model=list[CategoriaProductoConSubcategoriasResponse],
)
def listar_categorias_con_subcategorias_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ProductoService.listar_categorias_con_subcategorias_por_empresa(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar las categorias con subcategorias.")


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
    codigo_barra: str | None = Form(None),
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
            codigo_barra=codigo_barra,
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
