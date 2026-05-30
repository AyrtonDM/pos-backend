from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RegisterTokenIn(BaseModel):
    token: str
    uid_usuario: str | None = None
    rol: str | None = None
    plataforma: str | None = None
    id_empresa: int | None = None


@router.post("/register-token")
def register_token(payload: RegisterTokenIn, db: Session = Depends(get_db)):
    obj = NotificationRepository.add_token(db=db, token=payload.token, uid_usuario=payload.uid_usuario, rol=payload.rol, plataforma=payload.plataforma, id_empresa=payload.id_empresa)
    return {"ok": True, "token_id": obj.id}


class SendAlertIn(BaseModel):
    id_empresa: int
    titulo: str
    mensaje: str
    payload: dict | None = None


class MarkReadIn(BaseModel):
    id: int


@router.post("/send-alert")
def send_alert(req: SendAlertIn, db: Session = Depends(get_db)):
    res = NotificationService.enviar_alerta(db=db, id_empresa=req.id_empresa, titulo=req.titulo, mensaje=req.mensaje, payload=req.payload)
    return res


@router.get("/history/empresas/{id_empresa}")
def list_history(id_empresa: int, db: Session = Depends(get_db)):
    # explicit, unambiguous path parameter for empresa
    sql = text("SELECT * FROM notificaciones_historial WHERE id_empresa = :id_empresa")
    # some deployments store id_empresa as text; cast the param to string to avoid PG type mismatch
    res = db.execute(sql, {"id_empresa": str(id_empresa)}).mappings().all()
    return {"items": [dict(r) for r in res]}


@router.post('/mark-read')
def mark_read(payload: MarkReadIn, db: Session = Depends(get_db)):
    obj = NotificationRepository.mark_read(db=db, notif_id=payload.id)
    if not obj:
        raise HTTPException(status_code=404, detail='Notificacion no encontrada')
    return {"ok": True}
