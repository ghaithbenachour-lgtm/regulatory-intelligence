import pytest

from backend.app.ingestion.registry import registry
from backend.app.services.classifier import classify_article
from backend.app.ingestion.parsers import canonicalize_url, content_fingerprint


def test_registry_has_target_jurisdictions():
    codes = {j.code for j in registry.jurisdictions()}
    assert {"US", "SG", "HK", "AE", "ZA", "NG", "KE", "EU"}.issubset(codes)


def test_registry_sources_are_official():
    sources = registry.sources()
    assert len(sources) >= 10
    for source in sources:
        assert source.jurisdiction
        assert source.agency
        assert source.url.startswith("http")


def test_classifier_crypto_topic():
    result = classify_article(
        title="Consultation on virtual asset service providers",
        summary="The regulator proposes licensing rules for crypto exchanges.",
        jurisdiction="AE",
        default_topics=["crypto"],
    )
    assert "crypto" in result.topics


def test_classifier_ai_topic():
    result = classify_article(
        title="AI Act implementation guidance published",
        summary="Framework for artificial intelligence governance and compliance.",
        jurisdiction="EU",
        default_topics=["ai"],
    )
    assert "ai" in result.topics


def test_dedupe_fingerprint_stable():
    url = "https://www.sec.gov/news/example"
    fp1 = content_fingerprint("Title", "Summary", canonicalize_url(url))
    fp2 = content_fingerprint("Title", "Summary", canonicalize_url(url + "/"))
    assert fp1 == fp2
