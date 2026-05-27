import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import Article, ArticleTag, IngestionRun, Source
from backend.app.ingestion.parsers import (
    canonicalize_url,
    content_fingerprint,
    fetch_url,
    parse_html_list,
    parse_rss,
)
from backend.app.ingestion.registry import SourceDefinition, registry
from backend.app.services.classifier import classify_article
from backend.app.services.dedupe import is_duplicate


class IngestionPipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.lookback = timedelta(days=settings.ingest_lookback_days)

    def sync_sources_from_registry(self) -> None:
        for source_def in registry.sources():
            existing = self.db.get(Source, source_def.id)
            if existing:
                existing.name = source_def.name
                existing.agency = source_def.agency
                existing.jurisdiction = source_def.jurisdiction
                existing.url = source_def.url
                existing.feed_type = source_def.feed_type
                existing.html_selector = source_def.html_selector
            else:
                self.db.add(
                    Source(
                        id=source_def.id,
                        name=source_def.name,
                        agency=source_def.agency,
                        jurisdiction=source_def.jurisdiction,
                        url=source_def.url,
                        feed_type=source_def.feed_type,
                        html_selector=source_def.html_selector,
                    )
                )
        self.db.commit()

    async def _fetch_and_parse(self, source_def: SourceDefinition):
        content = await fetch_url(source_def.url)
        if source_def.feed_type == "rss":
            return parse_rss(content, source_def.url)
        return parse_html_list(content, source_def.url, source_def.html_selector or "a")

    async def _process_source(self, source: Source, source_def: SourceDefinition) -> tuple[int, int]:
        new_count = 0
        skipped = 0
        source.last_fetch_at = datetime.utcnow()
        try:
            parsed_articles = await self._fetch_and_parse(source_def)
            cutoff = datetime.utcnow() - self.lookback

            for parsed in parsed_articles:
                canonical = canonicalize_url(parsed.url)
                fingerprint = content_fingerprint(parsed.title, parsed.summary, canonical)

                if is_duplicate(self.db, canonical_url=canonical, content_fingerprint=fingerprint):
                    skipped += 1
                    continue

                if parsed.published_at and parsed.published_at.replace(tzinfo=None) < cutoff:
                    skipped += 1
                    continue

                classification = classify_article(
                    title=parsed.title,
                    summary=parsed.summary,
                    jurisdiction=source_def.jurisdiction,
                    default_topics=source_def.default_topics,
                )

                if not classification.topics:
                    skipped += 1
                    continue

                article = Article(
                    source_id=source.id,
                    title=parsed.title,
                    summary=parsed.summary,
                    canonical_url=canonical,
                    document_type=parsed.document_type,
                    published_at=parsed.published_at,
                    content_fingerprint=fingerprint,
                )
                self.db.add(article)
                self.db.flush()

                for topic in classification.topics:
                    self.db.add(
                        ArticleTag(
                            article_id=article.id,
                            jurisdiction=classification.jurisdiction,
                            topic=topic,
                            relevance_score=classification.scores.get(topic, 0.5),
                        )
                    )
                new_count += 1

            source.last_success_at = datetime.utcnow()
            source.last_error = None
            source.consecutive_failures = 0
            source.articles_fetched_total += new_count
            total_attempts = new_count + skipped
            if total_attempts:
                error_rate = skipped / total_attempts
                source.parse_error_rate = round(
                    (source.parse_error_rate * 0.7) + (error_rate * 0.3), 4
                )
        except Exception as exc:
            source.last_error = str(exc)[:2000]
            source.consecutive_failures = (source.consecutive_failures or 0) + 1
            raise
        finally:
            self.db.commit()
        return new_count, skipped

    async def run(self) -> IngestionRun:
        self.sync_sources_from_registry()
        run = IngestionRun(status="running")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        errors: list[str] = []
        total_new = 0
        total_skipped = 0
        processed = 0

        active_sources = self.db.query(Source).filter(Source.is_active.is_(True)).all()
        for source in active_sources:
            source_def = registry.get_source(source.id)
            if not source_def:
                continue
            processed += 1
            try:
                new_count, skipped = await self._process_source(source, source_def)
                total_new += new_count
                total_skipped += skipped
            except Exception as exc:
                errors.append(f"{source.id}: {exc}")

        run.finished_at = datetime.utcnow()
        run.status = "completed" if not errors else "completed_with_errors"
        run.sources_processed = processed
        run.articles_new = total_new
        run.articles_skipped = total_skipped
        run.errors = "\n".join(errors)
        self.db.commit()
        self.db.refresh(run)
        return run


def run_ingestion_sync(db: Session) -> IngestionRun:
    pipeline = IngestionPipeline(db)
    return asyncio.run(pipeline.run())
