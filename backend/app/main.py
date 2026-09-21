from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db import models
from app.db.database import SessionLocal, engine
from app.db.models import User
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.generation import router as generation_router
from app.routes.models import router as models_router
from app.routes.monitoring import router as monitoring_router
from app.routes.training import router as training_router

models.Base.metadata.create_all(bind=engine)


def create_default_admin() -> None:
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing is None:
            db.add(
                User(
                    email="admin@phoenixml.local",
                    username="admin",
                    hashed_password=hash_password("admin123"),
                    role="ADMIN",
                )
            )
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="PhoenixML production demo for model health monitoring and AIMD decision support.",
)


@app.on_event("startup")
def on_startup() -> None:
    create_default_admin()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(training_router, prefix="/api")
app.include_router(generation_router, prefix="/api")

frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")

trainer_dir = Path(__file__).resolve().parents[2] / "frontend" / "trainer"
if trainer_dir.exists():
    app.mount("/trainer", StaticFiles(directory=str(trainer_dir), html=True), name="trainer")


@app.get("/")
def root():
    return {"message": "PhoenixML backend is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
