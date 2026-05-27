from sqlalchemy.orm import Session

from backend.app.database import Article


def is_duplicate(
    db: Session,
    *,
    canonical_url: str,
    content_fingerprint: str,
) -> bool:
    existing = (
        db.query(Article)
        .filter(
            (Article.canonical_url == canonical_url)
            | (Article.content_fingerprint == content_fingerprint)
        )
        .first()
    )
    return existing is not None
