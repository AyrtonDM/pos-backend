from datetime import datetime
from pathlib import Path
import re
from typing import Optional


# Directorio base del proyecto (raíz del backend)
BASE_DIR = Path(__file__).resolve().parents[2]


def _sanitizar_nombre(nombre: str) -> str:
    """
    Sanitiza nombres para evitar caracteres inválidos en rutas de archivos/carpetas.
    
    Reemplaza caracteres especiales y normaliza espacios.
    
    Args:
        nombre: Nombre a sanitizar
        
    Returns:
        Nombre sanitizado seguro para usar en rutas
    """
    # Caracteres inválidos en Windows/Unix: < > : " / \ | ? *
    nombre_sanitizado = re.sub(r'[<>:"/\\|?*]', '_', nombre)
    # Remover espacios múltiples y normalizar
    nombre_sanitizado = ' '.join(nombre_sanitizado.split())
    return nombre_sanitizado.strip()


def registrar_accion(
    usuario_nombre: str,
    accion: str,
    empresa_nombre: Optional[str] = None,
    sucursal_nombre: Optional[str] = None
) -> None:
    """
    Registra una acción en la bitácora de archivos de texto.
    
    Agrega UNA SOLA LÍNEA al archivo de bitácora del usuario sin eliminar
    contenido anterior. Cada usuario tiene UN ÚNICO archivo .txt en:
        Bitacora/EmpresaNombre/SucursalNombre/NombreUsuario.txt
    
    IMPORTANTE: El nombre del archivo depende ÚNICAMENTE de usuario_nombre.
    La acción y la fecha NO se usan en el nombre del archivo.
    
    Todas las acciones se agregan como líneas nuevas al mismo archivo:
        [31-May-2026 15:10:00] Inició sesión
        [31-May-2026 15:15:22] Registró una venta con productos id: 1, 2
        [31-May-2026 15:20:45] Ingresó a inventario
    
    Args:
        usuario_nombre: Nombre del usuario que realizó la acción (REQUERIDO)
        accion: Descripción de la acción realizada (REQUERIDO)
        empresa_nombre: Nombre de la empresa. Si es None o vacío, usa "SinEmpresa"
        sucursal_nombre: Nombre de la sucursal. Si es None o vacío, usa "SinSucursal"
    """
    # Sanitizar parámetros de entrada
    empresa = (
        _sanitizar_nombre(empresa_nombre) 
        if empresa_nombre and empresa_nombre.strip() 
        else "SinEmpresa"
    )
    sucursal = (
        _sanitizar_nombre(sucursal_nombre) 
        if sucursal_nombre and sucursal_nombre.strip() 
        else "SinSucursal"
    )
    usuario = (
        _sanitizar_nombre(usuario_nombre) 
        if usuario_nombre and usuario_nombre.strip() 
        else "UsuarioDesconocido"
    )
    
    # Crear estructura de carpetas si no existen
    # Bitacora/Empresa/Sucursal/
    ruta_bitacora = BASE_DIR / "Bitacora" / empresa / sucursal
    ruta_bitacora.mkdir(parents=True, exist_ok=True)
    
    # ÚNICO archivo por usuario (nombre depende solo del usuario)
    # NO se crea un archivo nuevo por cada acción
    archivo_bitacora = ruta_bitacora / f"{usuario}.txt"
    
    # Generar timestamp
    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    
    # Limpiar la acción (remover espacios múltiples)
    accion_limpia = " ".join(accion.split())
    
    # Construir línea a agregar
    linea = f"[{timestamp}] {accion_limpia}\n"
    
    # Imprimir en consola con formato [BITACORA]
    print(f"[BITACORA] {empresa}/{sucursal}/{usuario}: [{timestamp}] {accion_limpia}")
    
    # APPEND MODE "a": Agrega la línea sin eliminar contenido anterior
    # Si el archivo no existe, se crea automáticamente
    # Si ya existe, se agrega la nueva línea al final
    with open(archivo_bitacora, "a", encoding="utf-8") as f:
        f.write(linea)
