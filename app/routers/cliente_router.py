# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.usuarios.usuario import Usuario
from app.schemas.cliente_schema import (
    CategoriaClienteCreate,
    CategoriaClienteResponse,
    CategoriaClienteUpdate,
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate,
)
from app.services.cliente_service import ClienteService
from app.services.bitacora_service import registrar_accion


cliente_router = APIRouter(prefix="/api/clientes", tags=["clientes"])
categoria_cliente_router = APIRouter(prefix="/api/categorias-cliente", tags=["categorias-cliente"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@categoria_cliente_router.post("/{id_empresa}", response_model=CategoriaClienteResponse)
def create_category(
    id_empresa: int,
    datos: CategoriaClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.crear_categoria_cliente(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            permite_credito=datos.permite_credito,
            descuento_base=datos.descuento_base,
            limite_credito=datos.limite_credito,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear la categoría de cliente.")


@categoria_cliente_router.get("/{id_empresa}", response_model=list[CategoriaClienteResponse])
def list_categories(
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
        raise HTTPException(status_code=500, detail="Error al listar las categorías de cliente.")


@categoria_cliente_router.get("/{id_empresa}/{id_categoria_cliente}", response_model=CategoriaClienteResponse)
def get_category(
    id_empresa: int,
    id_categoria_cliente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.obtener_categoria_cliente(
            db=db,
            current_user=current_user,
            id_empresa=id_empresa,
            id_categoria_cliente=id_categoria_cliente,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener la categoría de cliente.")


@categoria_cliente_router.put("/{id_empresa}/{id_categoria_cliente}", response_model=CategoriaClienteResponse)
def update_category(
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
        raise HTTPException(status_code=500, detail="Error al actualizar la categoría de cliente.")


@cliente_router.post("/{id_usuario}", response_model=ClienteResponse)
def create_client(
    id_usuario: int,
    datos: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = ClienteService.crear_cliente(
            db=db,
            current_user=current_user,
            id_usuario=id_usuario,
            id_categoria_cliente=datos.id_categoria_cliente,
            codigo_cliente=datos.codigo_cliente,
            saldo_credito=datos.saldo_credito,
            limite_credito=datos.limite_credito,
        )
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            registrar_accion(
                usuario_nombre=usuario_nombre,
                accion=f"Registró el cliente ID: {resultado.id_cliente}"
            )
        except Exception:
            pass
        return resultado  
        
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear el cliente.")


@cliente_router.get("/{id_usuario}", response_model=list[ClienteResponse])
def list_clients(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.listar_clientes(
            db=db,
            current_user=current_user,
            id_usuario=id_usuario,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al listar los clientes.")


@cliente_router.get("/{id_usuario}/{id_cliente}", response_model=ClienteResponse)
def get_client(
    id_usuario: int,
    id_cliente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return ClienteService.obtener_cliente(
            db=db,
            current_user=current_user,
            id_usuario=id_usuario,
            id_cliente=id_cliente,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener el cliente.")


@cliente_router.put("/{id_usuario}/{id_cliente}", response_model=ClienteResponse)
def update_client(
    id_usuario: int,
    id_cliente: int,
    datos: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        resultado = ClienteService.actualizar_cliente(
            db=db,
            current_user=current_user,
            id_usuario=id_usuario,
            id_cliente=id_cliente,
            id_categoria_cliente=datos.id_categoria_cliente,
            codigo_cliente=datos.codigo_cliente,
            saldo_credito=datos.saldo_credito,
            limite_credito=datos.limite_credito,
            activo=datos.activo,
        )
        #bitacora 
        try:
            usuario_nombre = getattr(current_user.persona, 'nombre_completo', None) if getattr(current_user, 'persona', None) else getattr(current_user, 'email', 'UsuarioDesconocido')
            registrar_accion(
                usuario_nombre=usuario_nombre,
                accion=f"Editó el cliente ID: {id_cliente}"
            )
        except Exception:
            pass
        return resultado

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar el cliente.")
