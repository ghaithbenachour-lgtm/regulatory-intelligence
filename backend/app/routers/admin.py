from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import IngestionRun, Source, get_db
from backend.app.ingestion.pipeline import run_ingestion_sync
from backend.app.schemas import IngestionRunOut, IngestTriggerResponse, SourceHealthOut

router = APIRouter(prefix="/api/admin", tags=["admin"])

STALE_HOURS = 36


@router.get("/health/sources", response_model=list[SourceHealthOut])
def source_health(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    stale_cutoff = now - timedelta(hours=STALE_HOURS)
    results: list[SourceHealthOut] = []

    for source in db.query(Source).order_by(Source.jurisdiction, Source.name).all():
        stale = source.is_active and (
            source.last_success_at is None or source.last_success_at < stale_cutoff
        )
        healthy = source.is_active and source.consecutive_failures == 0 and not stale
        results.append(
            SourceHealthOut(
                id=source.id,
                name=source.name,
                jurisdiction=source.jurisdiction,
                is_active=source.is_active,
                last_fetch_at=source.last_fetch_at,
                last_success_at=source.last_success_at,
                last_error=source.last_error,
                consecutive_failures=source.consecutive_failures or 0,
                stale=stale,
                healthy=healthy,
            )
        )
    return results


@router.get("/ingestion/runs", response_model=list[IngestionRunOut])
def ingestion_runs(limit: int = 20, db: Session = Depends(get_db)):
    runs = (
        db.query(IngestionRun)
        .order_by(IngestionRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return runs


@router.post("/ingestion/run", response_model=IngestTriggerResponse)
def trigger_ingestion(db: Session = Depends(get_db)):
    run = run_ingestion_sync(db)
    return IngestTriggerResponse(
        run_id=run.id,
        status=run.status,
        articles_new=run.articles_new,
        articles_skipped=run.articles_skipped,
    )
