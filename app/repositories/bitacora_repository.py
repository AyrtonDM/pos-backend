from sqlalchemy.orm import Session

from app.models.auditoria import Bitacora


class BitacoraRepository:
    @staticmethod
    def crear_registro(db: Session, datos: dict) -> Bitacora:
        """Crea un nuevo registro en la bitácora."""
        bitacora = Bitacora(**datos)
        db.add(bitacora)
        db.flush()
        db.refresh(bitacora)
        return bitacora

    @staticmethod
    def obtener_registros(db: Session, skip: int = 0, limit: int = 50) -> list[Bitacora]:
        """Obtiene registros de bitácora con paginación."""
        return (
            db.query(Bitacora)
            .order_by(Bitacora.fecha_hora.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_por_usuario(db: Session, id_usuario: int, skip: int = 0, limit: int = 50) -> list[Bitacora]:
        """Obtiene registros de bitácora de un usuario específico."""
        return (
            db.query(Bitacora)
            .filter(Bitacora.id_usuario == id_usuario)
            .order_by(Bitacora.fecha_hora.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_por_modulo(db: Session, modulo: str, skip: int = 0, limit: int = 50) -> list[Bitacora]:
        """Obtiene registros de bitácora de un módulo específico."""
        return (
            db.query(Bitacora)
            .filter(Bitacora.modulo == modulo)
            .order_by(Bitacora.fecha_hora.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_por_accion(db: Session, accion: str, skip: int = 0, limit: int = 50) -> list[Bitacora]:
        """Obtiene registros de bitácora de una acción específica."""
        return (
            db.query(Bitacora)
            .filter(Bitacora.accion == accion)
            .order_by(Bitacora.fecha_hora.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def contar_total(db: Session) -> int:
        """Retorna el total de registros en la bitácora."""
        return db.query(Bitacora).count()
