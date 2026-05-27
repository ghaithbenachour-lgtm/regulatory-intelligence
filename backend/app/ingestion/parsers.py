import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from backend.app.config import settings


@dataclass
class ParsedArticle:
    title: str
    summary: str
    url: str
    published_at: Optional[datetime] = None
    document_type: str = "news"


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def content_fingerprint(title: str, summary: str, url: str) -> str:
    normalized = re.sub(r"\s+", " ", f"{title} {summary} {url}".lower()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_datetime(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(value)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


async def fetch_url(url: str) -> str:
    headers = {"User-Agent": settings.user_agent}
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def parse_rss(content: str, base_url: str) -> list[ParsedArticle]:
    feed = feedparser.parse(content)
    articles: list[ParsedArticle] = []
    for entry in feed.entries[:50]:
        link = entry.get("link") or entry.get("id")
        if not link:
            continue
        if not link.startswith("http"):
            link = urljoin(base_url, link)
        summary = ""
        if entry.get("summary"):
            summary = BeautifulSoup(entry.summary, "lxml").get_text(" ", strip=True)[:1000]
        elif entry.get("description"):
            summary = BeautifulSoup(entry.description, "lxml").get_text(" ", strip=True)[:1000]
        published = None
        if entry.get("published"):
            published = parse_datetime(entry.published)
        elif entry.get("updated"):
            published = parse_datetime(entry.updated)
        articles.append(
            ParsedArticle(
                title=(entry.get("title") or "Untitled").strip(),
                summary=summary,
                url=link,
                published_at=published,
            )
        )
    return articles


def parse_html_list(content: str, base_url: str, selector: str = "a") -> list[ParsedArticle]:
    soup = BeautifulSoup(content, "lxml")
    seen: set[str] = set()
    articles: list[ParsedArticle] = []
    for anchor in soup.select(selector):
        href = anchor.get("href")
        title = anchor.get_text(" ", strip=True)
        if not href or not title or len(title) < 10:
            continue
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        url = href if href.startswith("http") else urljoin(base_url, href)
        canonical = canonicalize_url(url)
        if canonical in seen:
            continue
        seen.add(canonical)
        lower_title = title.lower()
        if any(skip in lower_title for skip in ("home", "contact", "privacy", "cookie", "login", "search")):
            continue
        articles.append(ParsedArticle(title=title[:1024], summary="", url=url))
        if len(articles) >= 40:
            break
    return articles
