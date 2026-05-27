import re
from dataclasses import dataclass

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "crypto": [
        "crypto",
        "cryptocurrency",
        "virtual asset",
        "digital asset",
        "bitcoin",
        "blockchain",
        "stablecoin",
        "token",
        "vasp",
        "defi",
        "nft",
        "web3",
        "mica",
        "digital currency",
    ],
    "tech": [
        "technology",
        "fintech",
        "digital",
        "cyber",
        "cybersecurity",
        "data protection",
        "privacy",
        "platform",
        "software",
        "cloud",
        "innovation",
        "electronic",
        "online",
        "internet",
        "telecom",
    ],
    "ai": [
        "artificial intelligence",
        " ai ",
        "machine learning",
        "generative",
        "llm",
        "large language model",
        "algorithm",
        "automated decision",
        "chatbot",
        "foundation model",
        "ai act",
        "ai governance",
    ],
}


@dataclass
class ClassificationResult:
    jurisdiction: str
    topics: list[str]
    scores: dict[str, float]


def _score_text(text: str, keywords: list[str]) -> float:
    lower = f" {text.lower()} "
    hits = sum(1 for kw in keywords if kw in lower)
    if hits == 0:
        return 0.0
    return min(1.0, hits / 3.0)


def classify_article(
    *,
    title: str,
    summary: str,
    jurisdiction: str,
    default_topics: list[str] | None = None,
    min_score: float = 0.34,
) -> ClassificationResult:
    text = f"{title} {summary}"
    scores: dict[str, float] = {}
    matched_topics: list[str] = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = _score_text(text, keywords)
        scores[topic] = score
        if score >= min_score:
            matched_topics.append(topic)

    if not matched_topics and default_topics:
        for topic in default_topics:
            if topic not in matched_topics:
                matched_topics.append(topic)
                scores[topic] = max(scores.get(topic, 0.0), 0.5)

    if not matched_topics:
        broad_regulatory = re.search(
            r"\b(regulation|regulatory|consultation|guidance|framework|licen[cs]e|compliance|supervision)\b",
            text,
            re.I,
        )
        if broad_regulatory and default_topics:
            matched_topics = list(default_topics)
            for topic in default_topics:
                scores[topic] = max(scores.get(topic, 0.0), 0.4)

    return ClassificationResult(jurisdiction=jurisdiction, topics=matched_topics, scores=scores)
