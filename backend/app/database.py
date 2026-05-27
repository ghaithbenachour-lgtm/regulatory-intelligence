from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from backend.app.config import settings


class Base(DeclarativeBase):
    pass


class Topic(str, Enum):
    CRYPTO = "crypto"
    TECH = "tech"
    AI = "ai"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    name = Column(String(200), default="")
    digest_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    digests = relationship("Digest", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "jurisdiction", "topic", name="uq_user_jurisdiction_topic"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jurisdiction = Column(String(10), nullable=False)
    topic = Column(String(20), nullable=False)

    user = relationship("User", back_populates="preferences")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    agency = Column(String(255), nullable=False)
    jurisdiction = Column(String(10), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    feed_type = Column(String(20), nullable=False)
    html_selector = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_fetch_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_error = Column(Text)
    consecutive_failures = Column(Integer, default=0)
    articles_fetched_total = Column(Integer, default=0)
    parse_error_rate = Column(Float, default=0.0)

    articles = relationship("Article", back_populates="source")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("canonical_url", name="uq_article_canonical_url"),)

    id = Column(Integer, primary_key=True)
    source_id = Column(String(64), ForeignKey("sources.id"), nullable=False, index=True)
    title = Column(String(1024), nullable=False)
    summary = Column(Text, default="")
    canonical_url = Column(String(2048), nullable=False)
    document_type = Column(String(64), default="news")
    published_at = Column(DateTime, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    content_fingerprint = Column(String(64), index=True)

    source = relationship("Source", back_populates="articles")
    tags = relationship("ArticleTag", back_populates="article", cascade="all, delete-orphan")


class ArticleTag(Base):
    __tablename__ = "article_tags"
    __table_args__ = (UniqueConstraint("article_id", "topic", name="uq_article_topic"),)

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True)
    topic = Column(String(20), nullable=False, index=True)
    relevance_score = Column(Float, default=1.0)

    article = relationship("Article", back_populates="tags")


class Digest(Base):
    __tablename__ = "digests"
    __table_args__ = (UniqueConstraint("user_id", "digest_date", name="uq_user_digest_date"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    digest_date = Column(String(10), nullable=False)
    subject = Column(String(512))
    body_plain = Column(Text)
    body_html = Column(Text)
    item_count = Column(Integer, default=0)
    sent_at = Column(DateTime)
    status = Column(String(32), default="pending")

    user = relationship("User", back_populates="digests")
    items = relationship("DigestItem", back_populates="digest", cascade="all, delete-orphan")


class DigestItem(Base):
    __tablename__ = "digest_items"

    id = Column(Integer, primary_key=True)
    digest_id = Column(Integer, ForeignKey("digests.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    jurisdiction = Column(String(10), nullable=False)
    topic = Column(String(20), nullable=False)
    sort_order = Column(Integer, default=0)

    digest = relationship("Digest", back_populates="items")
    article = relationship("Article")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    status = Column(String(32), default="running")
    sources_processed = Column(Integer, default=0)
    articles_new = Column(Integer, default=0)
    articles_skipped = Column(Integer, default=0)
    errors = Column(Text, default="")


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
