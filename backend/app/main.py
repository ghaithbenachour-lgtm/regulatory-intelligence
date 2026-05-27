from contextlib import asynccontextmanager
from pathlib import Path
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import SessionLocal, User, init_db
from backend.app.ingestion.pipeline import run_ingestion_sync
from backend.app.routers import admin, articles, digests
from backend.app.services.digest_builder import DigestBuilder
from backend.app.services.email_service import EmailService


def _run_scheduled_ingestion() -> None:
    db = SessionLocal()
    try:
        run_ingestion_sync(db)
    finally:
        db.close()


def _run_scheduled_digests() -> None:
    db = SessionLocal()
    try:
        builder = DigestBuilder(db)
        email_service = EmailService()
        users = db.query(User).filter(User.digest_enabled.is_(True)).all()
        for user in users:
            if not user.preferences:
                continue
            payload = builder.build_for_user(user)
            if payload["item_count"] == 0:
                continue
            digest = builder.persist_digest(user, payload, send=False)
            try:
                email_service.send_digest(
                    user.email, payload["subject"], payload["body_plain"], payload["body_html"]
                )
                from datetime import datetime

                digest.status = "sent"
                digest.sent_at = datetime.utcnow()
                db.commit()
            except Exception:
                digest.status = "failed"
                db.commit()
    finally:
        db.close()


scheduler = BackgroundScheduler()


def _maybe_run_initial_ingest() -> None:
    if not settings.run_initial_ingest:
        return
    db = SessionLocal()
    try:
        from backend.app.database import Article

        if db.query(Article).count() == 0:
            run_ingestion_sync(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    threading.Thread(target=_maybe_run_initial_ingest, daemon=True).start()
    scheduler.add_job(_run_scheduled_ingestion, "cron", hour=settings.ingest_cron_hour, id="ingest")
    scheduler.add_job(_run_scheduled_digests, "cron", hour=settings.digest_cron_hour, id="digest")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Regulatory Intelligence API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_origin_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(digests.router)
app.include_router(admin.router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
def admin_dashboard():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "regulatory-intelligence"}
