from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.models.usuarios import Persona, Rol, Usuario, UsuarioRol
from app.routers.auth_router import router as auth_router

app = FastAPI(title="POS Backend")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.on_event("startup")
def on_startup() -> None:
    # Importing models above registers all mapped tables in Base.metadata.
    Base.metadata.create_all(bind=engine)


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
