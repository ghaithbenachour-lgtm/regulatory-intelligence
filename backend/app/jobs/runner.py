"""CLI scripts for scheduled jobs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.database import SessionLocal, User, init_db
from backend.app.ingestion.pipeline import run_ingestion_sync
from backend.app.services.digest_builder import DigestBuilder
from backend.app.services.email_service import EmailService


def main_ingest() -> None:
    init_db()
    db = SessionLocal()
    try:
        run = run_ingestion_sync(db)
        print(
            f"Ingestion complete: status={run.status}, new={run.articles_new}, "
            f"skipped={run.articles_skipped}, sources={run.sources_processed}"
        )
    finally:
        db.close()


def main_send_digests() -> None:
    init_db()
    db = SessionLocal()
    try:
        builder = DigestBuilder(db)
        email_service = EmailService()
        users = db.query(User).filter(User.digest_enabled.is_(True)).all()
        sent = 0
        for user in users:
            if not user.preferences:
                continue
            payload = builder.build_for_user(user)
            if payload["item_count"] == 0:
                print(f"Skipping {user.email}: no matching articles")
                continue
            digest = builder.persist_digest(user, payload, send=False)
            email_service.send_digest(
                user.email, payload["subject"], payload["body_plain"], payload["body_html"]
            )
            from datetime import datetime

            digest.status = "sent"
            digest.sent_at = datetime.utcnow()
            db.commit()
            sent += 1
            print(f"Sent digest to {user.email} ({payload['item_count']} items)")
        print(f"Digests sent: {sent}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.app.jobs.runner [ingest|digest]")
        sys.exit(1)
    command = sys.argv[1]
    if command == "ingest":
        main_ingest()
    elif command == "digest":
        main_send_digests()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
