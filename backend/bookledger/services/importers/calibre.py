from collections.abc import Iterator
from pathlib import Path

from bookledger.services.importers.base import Importer, ImportedRecord


class CalibreImporter(Importer):
    source_kind = "calibre"

    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path
        self.metadata_db = library_path / "metadata.db"

    def fetch(self) -> Iterator[ImportedRecord]:
        raise NotImplementedError("calibre importer not implemented yet")
