from app.repositories.cliente_repository import ClienteRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.sucursal_repository import SucursalRepository
from app.repositories.usuario_repository import UsuarioRepository

__all__ = [
	"ClienteRepository",
	"EmpresaRepository",
	"InventarioRepository",
	"SucursalRepository",
	"UsuarioRepository",
	"ProductoRepository",
]
