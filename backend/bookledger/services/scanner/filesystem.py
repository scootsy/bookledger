from dataclasses import dataclass
from pathlib import Path


EBOOK_EXTS = {".epub", ".mobi", ".azw3", ".azw", ".pdf", ".cbz", ".cbr"}
AUDIOBOOK_EXTS = {".m4b", ".m4a", ".mp3", ".flac", ".ogg", ".opus"}


@dataclass
class ScanResult:
    path: Path
    kind: str
    extension: str
    size_bytes: int


def scan_root(root: Path) -> list[ScanResult]:
    raise NotImplementedError("filesystem scanner not implemented yet")
