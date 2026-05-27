import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REGISTRY_PATH = Path(__file__).resolve().parent / "sources.json"


@dataclass
class Jurisdiction:
    code: str
    name: str
    region: str


@dataclass
class SourceDefinition:
    id: str
    name: str
    agency: str
    jurisdiction: str
    url: str
    feed_type: Literal["rss", "html"]
    default_topics: list[str] = field(default_factory=list)
    html_selector: str | None = None


class SourceRegistry:
    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def jurisdictions(self) -> list[Jurisdiction]:
        return [Jurisdiction(**j) for j in self._data.get("jurisdictions", [])]

    def sources(self) -> list[SourceDefinition]:
        return [SourceDefinition(**s) for s in self._data.get("sources", [])]

    def get_source(self, source_id: str) -> SourceDefinition | None:
        for source in self.sources():
            if source.id == source_id:
                return source
        return None

    def sources_for_jurisdiction(self, jurisdiction_code: str) -> list[SourceDefinition]:
        return [s for s in self.sources() if s.jurisdiction == jurisdiction_code]


registry = SourceRegistry()
