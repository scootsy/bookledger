from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImportedRecord:
    source_kind: str
    source_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    asset_type: str = "ebook"
    asset_format: str | None = None
    asset_path: str | None = None
    identifiers: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class Importer(ABC):
    source_kind: str

    @abstractmethod
    def fetch(self) -> Iterator[ImportedRecord]:
        ...
