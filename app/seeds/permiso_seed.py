# -*- coding: utf-8 -*-
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.usuarios.modulo import Modulo
from app.models.usuarios.permiso import Permiso


DEFAULT_PERMISOS = [
    ("EMPRESAS", "EMPRESA_EDITAR", "Editar empresa"),
    ("EMPRESAS", "SUCURSAL_VER", "Ver sucursales"),
    ("EMPRESAS", "SUCURSAL_CREAR", "Crear sucursales"),
    ("EMPRESAS", "SUCURSAL_EDITAR", "Editar sucursales"),
    ("USUARIOS", "USUARIO_VER", "Ver usuarios"),
    ("USUARIOS", "USUARIO_CREAR", "Crear usuarios"),
    ("USUARIOS", "USUARIO_EDITAR", "Editar usuarios"),
    ("USUARIOS", "ROL_VER", "Ver roles"),
    ("USUARIOS", "ROL_CREAR", "Crear roles"),
    ("USUARIOS", "ROL_EDITAR", "Editar roles"),
    ("CLIENTES", "CLIENTE_VER", "Ver clientes"),
    ("CLIENTES", "CLIENTE_CREAR", "Crear clientes"),
    ("CLIENTES", "CLIENTE_EDITAR", "Editar clientes"),
    ("CLIENTES", "CATEGORIA_VER", "Ver categoria de clientes"),
    ("CLIENTES", "CATEGORIA_CREAR", "Crear categoria de clientes"),
    ("CLIENTES", "CATEGORIA_EDITAR", "Editar categoria de clientes"),
    ("INVENTARIO", "PRODUCTO_VER", "Ver productos"),
    ("INVENTARIO", "PRODUCTO_CREAR", "Crear productos"),
    ("INVENTARIO", "PRODUCTO_EDITAR", "Editar productos"),
    ("INVENTARIO", "STOCK_VER", "Ver stock"),
    ("INVENTARIO", "STOCK_CONFIGURAR", "Configurar niveles de stock"),
    ("INVENTARIO", "MOVIMIENTO_VER", "Ver movimientos de inventario"),
    ("INVENTARIO", "MOVIMIENTO_REGISTRAR", "Registrar movimientos de inventario"),
    ("INVENTARIO", "ALERTA_VER", "Ver alertas de stock minimo"),
    ("CAJAS", "CAJA_VER", "Ver cajas"),
    ("CAJAS", "CAJA_EDITAR", "Editar cajas"),
    ("CAJAS", "CAJA_ABRIR", "Abrir caja"),
    ("CAJAS", "CAJA_CERRAR", "Cerrar caja"),
    ("CAJAS", "MOVIMIENTO_VER", "Ver movimientos de caja"),
    ("CAJAS", "MOVIMIENTO_REGISTRAR", "Registrar movimientos de caja"),
    ("VENTAS", "VENTA_VER", "Ver ventas"),
    ("VENTAS", "VENTA_CREAR", "Crear ventas"),
    ("VENTAS", "VENTA_ANULAR", "Anular ventas"),
    ("VENTAS", "VENTA_DESCUENTO", "Aplicar descuento"),
    ("VENTAS", "FACTURA_EMITIR", "Emitir factura"),
    ("VENTAS", "FACTURA_REIMPRIMIR", "Reimprimir factura"),
    ("REPORTES", "REPORTE_GENERAR", "Generar reportes"),
    ("REPORTES", "REPORTE_EXPORTAR", "Exportar reportes"),
    ("REPORTES", "DASHBOARD_VER", "Ver dashboard"),
]


def seed_permisos(db: Session) -> None:
    db.execute(text("DROP INDEX IF EXISTS ix_permiso_codigo"))
    db.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_permiso_codigo_modulo "
            "ON permiso (codigo, id_modulo)"
        )
    )

    modulos = {modulo.codigo: modulo for modulo in db.query(Modulo).all()}

    for codigo_modulo, codigo_permiso, nombre_permiso in DEFAULT_PERMISOS:
        modulo = modulos.get(codigo_modulo)
        if not modulo:
            continue

        existe = (
            db.query(Permiso)
            .filter(Permiso.codigo == codigo_permiso, Permiso.id_modulo == modulo.id_modulo)
            .first()
        )
        if not existe:
            db.add(
                Permiso(
                    codigo=codigo_permiso,
                    nombre=nombre_permiso,
                    id_modulo=modulo.id_modulo,
                )
            )

    db.commit()
