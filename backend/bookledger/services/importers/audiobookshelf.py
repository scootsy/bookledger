from collections.abc import Iterator

from bookledger.services.importers.base import Importer, ImportedRecord


class AudiobookshelfImporter(Importer):
    source_kind = "audiobookshelf"

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def fetch(self) -> Iterator[ImportedRecord]:
        raise NotImplementedError("audiobookshelf importer not implemented yet")
