from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.rol_repository import RolRepository
from app.schemas.rol_schema import RolCreateResponse, RolDetalleResponse, RolPermisoResponse, RolResponse


class RolService:
    @staticmethod
    def listar_roles(db: Session, id_empresa: int):
        return RolRepository.obtener_roles(db=db, id_empresa=id_empresa)

    @staticmethod
    def obtener_rol_por_id(db: Session, id_rol: int) -> RolDetalleResponse:
        rol = RolRepository.obtener_rol_por_id(db=db, id_rol=id_rol)
        if rol is None:
            raise LookupError("No existe el rol solicitado.")

        rol_permisos = [
            RolPermisoResponse.model_validate(rol_permiso)
            for rol_permiso in sorted(rol.roles_permisos, key=lambda item: item.id_rol_permiso)
        ]

        return RolDetalleResponse(
            id_rol=rol.id_rol,
            nombre=rol.nombre,
            id_empresa=rol.id_empresa,
            tipo=rol.tipo,
            descripcion=rol.descripcion,
            activo=rol.activo,
            rol_permisos=rol_permisos,
        )

    @staticmethod
    def editar_rol(
        db: Session,
        id_rol: int,
        activo: bool,
        permiso_ids: list[int],
    ) -> RolDetalleResponse:
        rol = RolRepository.obtener_rol_por_id(db=db, id_rol=id_rol)
        if rol is None:
            raise LookupError("No existe el rol solicitado.")

        permiso_ids_unicos = list(dict.fromkeys(permiso_ids))
        for id_permiso in permiso_ids_unicos:
            permiso = RolRepository.obtener_permiso_por_id(db=db, id_permiso=id_permiso)
            if permiso is None:
                raise ValueError(f"No existe el permiso con id {id_permiso}.")

        try:
            estaba_activo = rol.activo
            rol.activo = activo

            rol_permisos_por_permiso_id = {
                rp.id_permiso: rp
                for rp in rol.roles_permisos
            }

            if not activo:
                for rol_permiso in rol_permisos_por_permiso_id.values():
                    rol_permiso.activo = False
            # Si se reactiva y no enviaron permisos, se reactivan todos los existentes.
            elif (not estaba_activo) and (not permiso_ids_unicos):
                for rol_permiso in rol_permisos_por_permiso_id.values():
                    rol_permiso.activo = True
            else:
                # Permisos enviados: si no existen se crean, si existen y estaban inactivos se activan.
                for id_permiso in permiso_ids_unicos:
                    rol_permiso = rol_permisos_por_permiso_id.get(id_permiso)
                    if rol_permiso is None:
                        nuevo_rol_permiso = RolRepository.crear_rol_permiso(
                            db=db,
                            id_rol=rol.id_rol,
                            id_permiso=id_permiso,
                        )
                        rol_permisos_por_permiso_id[id_permiso] = nuevo_rol_permiso
                    else:
                        rol_permiso.activo = True

                # Permisos no enviados: se desactivan si existen para ese rol.
                permisos_enviados = set(permiso_ids_unicos)
                for id_permiso, rol_permiso in rol_permisos_por_permiso_id.items():
                    if id_permiso not in permisos_enviados:
                        rol_permiso.activo = False

            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("No se pudo editar el rol.") from exc
        except Exception:
            db.rollback()
            raise

        return RolService.obtener_rol_por_id(db=db, id_rol=id_rol)

    @staticmethod
    def crear_rol_con_permisos(
        db: Session,
        id_empresa: int,
        nombre: str,
        permiso_ids: list[int],
    ) -> RolCreateResponse:
        nombre_normalizado = nombre.strip().upper()
        permiso_ids_unicos = list(dict.fromkeys(permiso_ids))

        permisos = []
        for id_permiso in permiso_ids_unicos:
            permiso = RolRepository.obtener_permiso_por_id(db=db, id_permiso=id_permiso)
            if permiso is None:
                raise ValueError(f"No existe el permiso con id {id_permiso}.")
            permisos.append(permiso)

        try:
            rol = RolRepository.crear_rol(
                db=db,
                datos={
                    "nombre": nombre_normalizado,
                    "id_empresa": id_empresa,
                    "tipo": "INTERNO",
                    "descripcion": nombre_normalizado,
                    "activo": True,
                },
            )

            for permiso in permisos:
                RolRepository.crear_rol_permiso(
                    db=db,
                    id_rol=rol.id_rol,
                    id_permiso=permiso.id_permiso,
                )

            db.commit()
            db.refresh(rol)

            return RolCreateResponse(
                rol=RolResponse.model_validate(rol),
                permiso_ids=permiso_ids_unicos,
            )
        except IntegrityError as exc:
            db.rollback()
            raise ValueError(
                "No se pudo crear el rol. Verifique que el nombre no exista en esta empresa."
            ) from exc
        except Exception:
            db.rollback()
            raise
