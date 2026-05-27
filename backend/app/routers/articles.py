from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.database import Article, ArticleTag, Source, User, UserPreference, get_db
from backend.app.ingestion.registry import registry
from backend.app.schemas import (
    ArticleFeedResponse,
    ArticleOut,
    ArticleTagOut,
    JurisdictionOut,
    PreferenceIn,
    SourceOut,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/api", tags=["core"])


def _article_to_out(article: Article) -> ArticleOut:
    return ArticleOut(
        id=article.id,
        source_id=article.source_id,
        title=article.title,
        summary=article.summary,
        canonical_url=article.canonical_url,
        document_type=article.document_type,
        published_at=article.published_at,
        fetched_at=article.fetched_at,
        source_name=article.source.name if article.source else None,
        agency=article.source.agency if article.source else None,
        tags=[ArticleTagOut.model_validate(t) for t in article.tags],
    )


@router.get("/jurisdictions", response_model=list[JurisdictionOut])
def list_jurisdictions():
    return [JurisdictionOut(**j.__dict__) for j in registry.jurisdictions()]


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.jurisdiction, Source.name).all()


@router.get("/articles", response_model=ArticleFeedResponse)
def list_articles(
    jurisdictions: list[str] | None = Query(default=None),
    topics: list[str] | None = Query(default=None),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Article)
        .join(ArticleTag)
        .options(joinedload(Article.tags), joinedload(Article.source))
    )

    if jurisdictions:
        query = query.filter(ArticleTag.jurisdiction.in_(jurisdictions))
    if topics:
        query = query.filter(ArticleTag.topic.in_(topics))
    if date_from:
        query = query.filter(Article.published_at >= date_from)
    if date_to:
        query = query.filter(Article.published_at <= date_to)

    query = query.distinct(Article.id).order_by(
        Article.published_at.desc().nullslast(), Article.fetched_at.desc()
    )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ArticleFeedResponse(
        items=[_article_to_out(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users", response_model=UserOut)
def create_or_update_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(email=payload.email, name=payload.name)
        db.add(user)
        db.flush()
    else:
        user.name = payload.name

    db.query(UserPreference).filter(UserPreference.user_id == user.id).delete()
    for pref in payload.preferences:
        db.add(
            UserPreference(
                user_id=user.id,
                jurisdiction=pref.jurisdiction,
                topic=pref.topic,
            )
        )
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        digest_enabled=user.digest_enabled,
        preferences=[PreferenceIn(jurisdiction=p.jurisdiction, topic=p.topic) for p in user.preferences],
    )


@router.get("/users/{email}", response_model=UserOut)
def get_user(email: str, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.preferences)).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        digest_enabled=user.digest_enabled,
        preferences=[PreferenceIn(jurisdiction=p.jurisdiction, topic=p.topic) for p in user.preferences],
    )
