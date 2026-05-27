from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class JurisdictionOut(BaseModel):
    code: str
    name: str
    region: str


class SourceOut(BaseModel):
    id: str
    name: str
    agency: str
    jurisdiction: str
    url: str
    feed_type: str
    is_active: bool
    last_fetch_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    articles_fetched_total: int = 0
    parse_error_rate: float = 0.0

    model_config = {"from_attributes": True}


class ArticleTagOut(BaseModel):
    jurisdiction: str
    topic: str
    relevance_score: float

    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id: int
    source_id: str
    title: str
    summary: str
    canonical_url: str
    document_type: str
    published_at: Optional[datetime] = None
    fetched_at: datetime
    source_name: Optional[str] = None
    agency: Optional[str] = None
    tags: list[ArticleTagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ArticleFeedResponse(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    page_size: int


class PreferenceIn(BaseModel):
    jurisdiction: str
    topic: str


class UserCreate(BaseModel):
    email: EmailStr
    name: str = ""
    preferences: list[PreferenceIn] = Field(default_factory=list)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    digest_enabled: bool
    preferences: list[PreferenceIn]

    model_config = {"from_attributes": True}


class DigestOut(BaseModel):
    id: int
    digest_date: str
    subject: Optional[str] = None
    item_count: int
    sent_at: Optional[datetime] = None
    status: str

    model_config = {"from_attributes": True}


class DigestPreviewOut(BaseModel):
    subject: str
    body_plain: str
    body_html: str
    item_count: int
    sections: dict[str, dict[str, list[ArticleOut]]]


class SourceHealthOut(BaseModel):
    id: str
    name: str
    jurisdiction: str
    is_active: bool
    last_fetch_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int
    stale: bool
    healthy: bool

    model_config = {"from_attributes": True}


class IngestionRunOut(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    sources_processed: int
    articles_new: int
    articles_skipped: int
    errors: str

    model_config = {"from_attributes": True}


class IngestTriggerResponse(BaseModel):
    run_id: int
    status: str
    articles_new: int
    articles_skipped: int
