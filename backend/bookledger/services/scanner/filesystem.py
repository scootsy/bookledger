"""Filesystem scanner for ebook and audiobook libraries.

Read-only contract: every file operation in this module reads. Files are
never created, modified, or deleted, and `open()` is only ever called in
binary read mode ("rb"). External libraries used here (zipfile, mutagen)
are also called in their read-only modes. This is enforced by:

1. Library volumes being mounted read-only (`:ro`) in docker-compose.
2. The kernel rejecting any write attempt against those mounts.
3. The code paths here never invoking any write/delete syscall.

Do not add write operations to this module. If a future feature requires
writing (e.g. generating thumbnails), put it in a separate module with
its own writable cache directory under /config.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from bookledger.services.scanner.metadata import (
    read_audio_metadata,
    read_epub_metadata,
)

EBOOK_EXTS = frozenset({".epub", ".mobi", ".azw3", ".azw", ".pdf", ".cbz", ".cbr"})
AUDIOBOOK_EXTS = frozenset({".m4b", ".m4a", ".mp3", ".flac", ".ogg", ".opus"})

_QUICK_HASH_BYTES = 65536
_YEAR_RE = re.compile(r"[\(\[](\d{4})[\)\]]")
_SERIES_POS_RE = re.compile(r"\b(?:book|vol(?:ume)?|#)\s*(\d+(?:\.\d+)?)\b", re.IGNORECASE)
_AUTHOR_TITLE_SEP_RE = re.compile(r"\s+[-–—]\s+")
_PAREN_STRIP_RE = re.compile(r"\s*[\(\[].*?[\)\]]\s*")


@dataclass
class ScannedAsset:
    path: Path
    type: str
    format: str
    content_hash: str
    size_bytes: int
    duration_seconds: int | None = None
    page_count: int | None = None
    bitrate: int | None = None
    narrator: str | None = None
    title_hint: str | None = None
    author_hint: str | None = None
    series_hint: str | None = None
    series_position_hint: float | None = None
    publication_year_hint: int | None = None
    identifiers: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


def quick_hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(str(path.stat().st_size).encode())
    h.update(b"\0")
    with open(path, "rb") as f:
        h.update(f.read(_QUICK_HASH_BYTES))
    return h.hexdigest()


def quick_hash_directory(files: list[Path]) -> str:
    h = hashlib.sha256()
    for f in sorted(files):
        h.update(f.name.encode())
        h.update(b"\0")
        h.update(str(f.stat().st_size).encode())
        h.update(b"\0")
    return h.hexdigest()


def _parse_path_hints(root: Path, file_path: Path) -> dict[str, Any]:
    try:
        rel = file_path.relative_to(root)
    except ValueError:
        return {}
    parts = list(rel.parts)
    if not parts:
        return {}
    stem = file_path.stem
    out: dict[str, Any] = {}

    search_targets = [stem]
    if len(parts) >= 2:
        search_targets.append(parts[-2])

    for target in search_targets:
        m = _YEAR_RE.search(target)
        if m:
            try:
                year = int(m.group(1))
                if 1500 <= year <= 2100:
                    out["publication_year"] = year
                    break
            except ValueError:
                pass

    for target in search_targets:
        m = _SERIES_POS_RE.search(target)
        if m:
            try:
                out["series_position"] = float(m.group(1))
                break
            except ValueError:
                pass

    if len(parts) >= 2:
        out["author_hint"] = parts[0].strip()
        out["title_hint"] = _PAREN_STRIP_RE.sub(" ", parts[-2]).strip()
    else:
        m = _AUTHOR_TITLE_SEP_RE.search(stem)
        if m:
            a, t = _AUTHOR_TITLE_SEP_RE.split(stem, maxsplit=1)
            out["author_hint"] = a.strip()
            out["title_hint"] = _PAREN_STRIP_RE.sub(" ", t).strip()
        else:
            out["title_hint"] = _PAREN_STRIP_RE.sub(" ", stem).strip()

    return out


def _parse_directory_hints(root: Path, directory: Path) -> dict[str, Any]:
    try:
        rel = directory.relative_to(root)
    except ValueError:
        return {}
    parts = list(rel.parts)
    out: dict[str, Any] = {}
    if not parts:
        return out
    if len(parts) >= 2:
        out["author_hint"] = parts[0].strip()
        out["title_hint"] = _PAREN_STRIP_RE.sub(" ", parts[-1]).strip()
    else:
        out["title_hint"] = _PAREN_STRIP_RE.sub(" ", parts[0]).strip()
    for target in [parts[-1]] + ([parts[-2]] if len(parts) >= 2 else []):
        m = _YEAR_RE.search(target)
        if m:
            try:
                year = int(m.group(1))
                if 1500 <= year <= 2100:
                    out["publication_year"] = year
                    break
            except ValueError:
                pass
        m = _SERIES_POS_RE.search(target)
        if m:
            try:
                out["series_position"] = float(m.group(1))
                break
            except ValueError:
                pass
    return out


def scan_ebook_root(root: Path) -> Iterator[ScannedAsset]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in EBOOK_EXTS:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size == 0:
            continue
        hints = _parse_path_hints(root, path)
        embedded: dict[str, Any] = {}
        if ext == ".epub":
            embedded = read_epub_metadata(path)

        title = embedded.get("title") or hints.get("title_hint")
        authors_list = embedded.get("authors") or (
            [hints["author_hint"]] if hints.get("author_hint") else []
        )
        author_str = ", ".join(authors_list) if authors_list else None

        yield ScannedAsset(
            path=path,
            type="ebook",
            format=ext.lstrip("."),
            content_hash=quick_hash_file(path),
            size_bytes=size,
            title_hint=title,
            author_hint=author_str,
            series_hint=hints.get("series_hint"),
            series_position_hint=hints.get("series_position"),
            publication_year_hint=embedded.get("publication_year") or hints.get("publication_year"),
            identifiers=embedded.get("identifiers", {}),
            extra={"embedded": embedded, "path_hints": hints},
        )


def scan_audiobook_root(root: Path) -> Iterator[ScannedAsset]:
    by_dir: dict[Path, list[Path]] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in AUDIOBOOK_EXTS:
            continue
        by_dir.setdefault(path.parent, []).append(path)

    for directory, files in by_dir.items():
        files.sort()
        try:
            total_size = sum(f.stat().st_size for f in files)
        except OSError:
            continue
        if total_size == 0:
            continue

        format_counts: dict[str, int] = {}
        for f in files:
            ext = f.suffix.lower().lstrip(".")
            format_counts[ext] = format_counts.get(ext, 0) + 1
        primary_format = max(format_counts, key=lambda k: format_counts[k])

        first_meta = read_audio_metadata(files[0])
        total_duration = 0
        for f in files:
            meta = read_audio_metadata(f) if f != files[0] else first_meta
            d = meta.get("duration_seconds")
            if isinstance(d, (int, float)) and d > 0:
                total_duration += int(d)

        hints = _parse_directory_hints(root, directory)
        title = first_meta.get("album") or first_meta.get("title") or hints.get("title_hint")
        author = first_meta.get("author") or hints.get("author_hint")

        yield ScannedAsset(
            path=directory,
            type="audiobook",
            format=primary_format,
            content_hash=quick_hash_directory(files),
            size_bytes=total_size,
            duration_seconds=total_duration or None,
            bitrate=first_meta.get("bitrate"),
            narrator=first_meta.get("narrator"),
            title_hint=title,
            author_hint=author,
            series_hint=hints.get("series_hint"),
            series_position_hint=hints.get("series_position"),
            publication_year_hint=hints.get("publication_year"),
            extra={
                "embedded": first_meta,
                "file_count": len(files),
                "files": [str(f.relative_to(root)) for f in files],
            },
        )


def scan_root(root: Path, kind: str) -> Iterator[ScannedAsset]:
    if kind == "ebook":
        yield from scan_ebook_root(root)
    elif kind == "audiobook":
        yield from scan_audiobook_root(root)
    else:
        raise ValueError(f"unknown library root kind: {kind}")
