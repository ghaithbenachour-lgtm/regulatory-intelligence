import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import settings
from backend.app.database import SessionLocal, User, UserPreference, init_db
from backend.app.ingestion.pipeline import run_ingestion_sync


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        run_ingestion_sync(db)

        email = settings.default_digest_email or "demo@example.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name="Demo User", digest_enabled=True)
            db.add(user)
            db.flush()

        defaults = [
            ("US", "crypto"),
            ("US", "ai"),
            ("SG", "crypto"),
            ("HK", "crypto"),
            ("AE", "crypto"),
            ("ZA", "tech"),
            ("EU", "ai"),
        ]
        db.query(UserPreference).filter(UserPreference.user_id == user.id).delete()
        for jurisdiction, topic in defaults:
            db.add(
                UserPreference(user_id=user.id, jurisdiction=jurisdiction, topic=topic)
            )
        db.commit()
        print(f"Seeded user {email} with {len(defaults)} preferences")
        print("Initial ingestion completed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
