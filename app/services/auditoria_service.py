from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.bitacora_repository import BitacoraRepository


class AuditoriaService:
    @staticmethod
    def registrar_evento(
        db: Session,
        id_usuario: int | None,
        accion: str,
        modulo: str,
        descripcion: str | None = None,
        ip: str | None = None,
    ) -> dict:
        """
        Registra un evento en la bitácora.

        Args:
            db: Sesión de base de datos
            id_usuario: ID del usuario que realizó la acción (nullable)
            accion: Tipo de acción (CREATE, READ, UPDATE, DELETE, LOGIN, etc)
            modulo: Módulo donde ocurrió (usuarios, productos, ventas, etc)
            descripcion: Descripción detallada del evento (opcional)
            ip: Dirección IP del cliente (opcional)

        Returns:
            Dict con los datos del registro creado
        """
        try:
            datos = {
                "id_usuario": id_usuario,
                "accion": accion,
                "modulo": modulo,
                "descripcion": descripcion,
                "ip": ip,
                "fecha_hora": datetime.utcnow(),
            }

            bitacora = BitacoraRepository.crear_registro(db=db, datos=datos)
            db.commit()

            return {
                "id_bitacora": bitacora.id_bitacora,
                "id_usuario": bitacora.id_usuario,
                "accion": bitacora.accion,
                "modulo": bitacora.modulo,
                "descripcion": bitacora.descripcion,
                "ip": bitacora.ip,
                "fecha_hora": bitacora.fecha_hora,
                "mensaje": "Evento registrado exitosamente",
            }
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al registrar evento en bitácora: {str(e)}")

    @staticmethod
    def obtener_bitacora(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        id_usuario: int | None = None,
        modulo: str | None = None,
        accion: str | None = None,
    ) -> dict:
        """
        Obtiene registros de la bitácora con filtros opcionales.

        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número de registros a retornar
            id_usuario: Filtrar por usuario (opcional)
            modulo: Filtrar por módulo (opcional)
            accion: Filtrar por acción (opcional)

        Returns:
            Dict con registros y metadatos de paginación
        """
        try:
            if id_usuario:
                registros = BitacoraRepository.obtener_por_usuario(
                    db=db, id_usuario=id_usuario, skip=skip, limit=limit
                )
            elif modulo:
                registros = BitacoraRepository.obtener_por_modulo(
                    db=db, modulo=modulo, skip=skip, limit=limit
                )
            elif accion:
                registros = BitacoraRepository.obtener_por_accion(
                    db=db, accion=accion, skip=skip, limit=limit
                )
            else:
                registros = BitacoraRepository.obtener_registros(db=db, skip=skip, limit=limit)

            total = BitacoraRepository.contar_total(db=db)

            return {
                "registros": registros,
                "total": total,
                "skip": skip,
                "limit": limit,
                "paginas": (total + limit - 1) // limit,
            }
        except Exception as e:
            raise ValueError(f"Error al obtener bitácora: {str(e)}")
