from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.database import Digest, User, get_db
from backend.app.schemas import DigestOut, DigestPreviewOut, ArticleOut
from backend.app.services.digest_builder import DigestBuilder
from backend.app.services.email_service import EmailService

router = APIRouter(prefix="/api/digests", tags=["digests"])


@router.get("/preview/{email}", response_model=DigestPreviewOut)
def preview_digest(email: str, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.preferences)).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    builder = DigestBuilder(db)
    payload = builder.build_for_user(user)

    sections_out: dict[str, dict[str, list[ArticleOut]]] = {}
    for jurisdiction, topics in payload["sections"].items():
        sections_out[jurisdiction] = {}
        for topic, items in topics.items():
            sections_out[jurisdiction][topic] = items

    return DigestPreviewOut(
        subject=payload["subject"],
        body_plain=payload["body_plain"],
        body_html=payload["body_html"],
        item_count=payload["item_count"],
        sections=sections_out,
    )


@router.post("/send/{email}", response_model=DigestOut)
def send_digest(email: str, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.preferences)).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.digest_enabled:
        raise HTTPException(status_code=400, detail="Digest disabled for user")

    builder = DigestBuilder(db)
    payload = builder.build_for_user(user)
    digest = builder.persist_digest(user, payload, send=False)

    email_service = EmailService()
    email_service.send_digest(user.email, payload["subject"], payload["body_plain"], payload["body_html"])
    digest.status = "sent"
    from datetime import datetime

    digest.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(digest)

    return DigestOut(
        id=digest.id,
        digest_date=digest.digest_date,
        subject=digest.subject,
        item_count=digest.item_count,
        sent_at=digest.sent_at,
        status=digest.status,
    )


@router.get("/history/{email}", response_model=list[DigestOut])
def digest_history(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    digests = (
        db.query(Digest)
        .filter(Digest.user_id == user.id)
        .order_by(Digest.digest_date.desc())
        .limit(30)
        .all()
    )
    return [
        DigestOut(
            id=d.id,
            digest_date=d.digest_date,
            subject=d.subject,
            item_count=d.item_count,
            sent_at=d.sent_at,
            status=d.status,
        )
        for d in digests
    ]
