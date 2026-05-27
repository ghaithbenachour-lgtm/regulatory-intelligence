from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from backend.app.database import Article, ArticleTag, Digest, DigestItem, User, UserPreference
from backend.app.schemas import ArticleOut, ArticleTagOut


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


class DigestBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _matching_articles(self, user: User, since: datetime) -> list[Article]:
        prefs = user.preferences
        if not prefs:
            return []

        jurisdiction_set = {p.jurisdiction for p in prefs}
        topic_set = {p.topic for p in prefs}

        query = (
            self.db.query(Article)
            .join(ArticleTag)
            .options(joinedload(Article.tags), joinedload(Article.source))
            .filter(ArticleTag.jurisdiction.in_(jurisdiction_set))
            .filter(ArticleTag.topic.in_(topic_set))
            .filter(Article.fetched_at >= since)
            .order_by(Article.published_at.desc().nullslast(), Article.fetched_at.desc())
        )
        articles = query.all()

        filtered: list[Article] = []
        seen_ids: set[int] = set()
        pref_pairs = {(p.jurisdiction, p.topic) for p in prefs}

        for article in articles:
            if article.id in seen_ids:
                continue
            article_pairs = {(t.jurisdiction, t.topic) for t in article.tags}
            if article_pairs & pref_pairs:
                filtered.append(article)
                seen_ids.add(article.id)
        return filtered

    def build_for_user(self, user: User, digest_date: str | None = None) -> dict:
        digest_date = digest_date or datetime.utcnow().strftime("%Y-%m-%d")
        since = datetime.utcnow() - timedelta(hours=24)
        articles = self._matching_articles(user, since)

        sections: dict[str, dict[str, list[ArticleOut]]] = defaultdict(lambda: defaultdict(list))
        for article in articles:
            article_out = _article_to_out(article)
            for tag in article.tags:
                pref_pairs = {(p.jurisdiction, p.topic) for p in user.preferences}
                if (tag.jurisdiction, tag.topic) in pref_pairs:
                    sections[tag.jurisdiction][tag.topic].append(article_out)

        subject = f"Regulatory Digest — {digest_date} ({len(articles)} updates)"
        lines = [f"Daily Regulatory Intelligence Digest — {digest_date}", ""]
        html_parts = [
            f"<h1>Daily Regulatory Intelligence Digest</h1><p><strong>{digest_date}</strong></p>"
        ]

        if not articles:
            lines.append("No new official regulatory updates matched your preferences in the last 24 hours.")
            html_parts.append("<p>No new official regulatory updates matched your preferences in the last 24 hours.</p>")
        else:
            for jurisdiction in sorted(sections.keys()):
                lines.append(f"## {jurisdiction}")
                html_parts.append(f"<h2>{jurisdiction}</h2>")
                for topic in sorted(sections[jurisdiction].keys()):
                    lines.append(f"### {topic.upper()}")
                    html_parts.append(f"<h3>{topic.upper()}</h3><ul>")
                    for item in sections[jurisdiction][topic]:
                        agency = item.agency or item.source_name or "Official source"
                        lines.append(f"- [{item.title}]({item.canonical_url})")
                        lines.append(f"  Source: {agency}")
                        html_parts.append(
                            f"<li><a href=\"{item.canonical_url}\">{item.title}</a>"
                            f"<br><small>{agency}</small></li>"
                        )
                    html_parts.append("</ul>")

        lines.extend(["", "---", "Official sources only. Links point to regulator publications."])
        html_parts.append("<hr><p><small>Official sources only. Links point to regulator publications.</small></p>")

        return {
            "digest_date": digest_date,
            "subject": subject,
            "body_plain": "\n".join(lines),
            "body_html": "".join(html_parts),
            "item_count": len(articles),
            "sections": sections,
            "articles": articles,
        }

    def persist_digest(self, user: User, payload: dict, *, send: bool = False) -> Digest:
        existing = (
            self.db.query(Digest)
            .filter(Digest.user_id == user.id, Digest.digest_date == payload["digest_date"])
            .first()
        )
        if existing:
            digest = existing
            self.db.query(DigestItem).filter(DigestItem.digest_id == digest.id).delete()
        else:
            digest = Digest(user_id=user.id, digest_date=payload["digest_date"])
            self.db.add(digest)
            self.db.flush()

        digest.subject = payload["subject"]
        digest.body_plain = payload["body_plain"]
        digest.body_html = payload["body_html"]
        digest.item_count = payload["item_count"]
        digest.status = "pending"

        sort_order = 0
        for jurisdiction, topics in payload["sections"].items():
            for topic, items in topics.items():
                for item in items:
                    self.db.add(
                        DigestItem(
                            digest_id=digest.id,
                            article_id=item.id,
                            jurisdiction=jurisdiction,
                            topic=topic,
                            sort_order=sort_order,
                        )
                    )
                    sort_order += 1

        if send:
            digest.sent_at = datetime.utcnow()
            digest.status = "sent"
        self.db.commit()
        self.db.refresh(digest)
        return digest
