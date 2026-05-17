from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from bookledger.models import Asset, LibraryRoot, ReviewItem
from bookledger.services.matcher.engine import (
    MatchInput,
    MatchLevel,
    create_work_from_match,
    find_match,
)
from bookledger.services.scanner.filesystem import ScannedAsset, scan_root

logger = logging.getLogger(__name__)


@dataclass
class ScanStats:
    files_seen: int = 0
    assets_added: int = 0
    assets_updated: int = 0
    works_created: int = 0
    review_items_created: int = 0
    errors: list[str] = field(default_factory=list)


def scan_library_root(session: Session, root: LibraryRoot) -> ScanStats:
    stats = ScanStats()
    root_path = Path(root.path)

    if not root_path.exists():
        stats.errors.append(f"Path does not exist: {root_path}")
        return stats
    if not root_path.is_dir():
        stats.errors.append(f"Path is not a directory: {root_path}")
        return stats

    for scanned in scan_root(root_path, root.kind):
        stats.files_seen += 1
        try:
            _process_scanned_asset(session, root, scanned, stats)
        except Exception as exc:
            logger.exception("scan error on %s", scanned.path)
            stats.errors.append(f"{scanned.path}: {exc}")
            session.rollback()

    root.last_scanned_at = datetime.utcnow()
    session.add(root)
    session.commit()
    return stats


def _process_scanned_asset(
    session: Session,
    root: LibraryRoot,
    scanned: ScannedAsset,
    stats: ScanStats,
) -> None:
    path_str = str(scanned.path)
    existing = session.exec(
        select(Asset).where(Asset.source_kind == "filesystem", Asset.path == path_str)
    ).first()

    metadata_blob = _build_metadata_blob(root, scanned)

    if existing:
        existing.content_hash = scanned.content_hash
        existing.size_bytes = scanned.size_bytes
        existing.duration_seconds = scanned.duration_seconds
        existing.bitrate = scanned.bitrate
        existing.narrator = scanned.narrator
        existing.format = scanned.format
        existing.last_seen = datetime.utcnow()
        existing.metadata_blob = metadata_blob
        session.add(existing)
        session.commit()
        stats.assets_updated += 1
        return

    asset = Asset(
        work_id=None,
        type=scanned.type,
        format=scanned.format,
        source_kind="filesystem",
        source_id=str(root.id),
        path=path_str,
        content_hash=scanned.content_hash,
        size_bytes=scanned.size_bytes,
        duration_seconds=scanned.duration_seconds,
        bitrate=scanned.bitrate,
        narrator=scanned.narrator,
        metadata_blob=metadata_blob,
    )
    session.add(asset)
    session.flush()

    if scanned.title_hint:
        inp = MatchInput(
            title=scanned.title_hint,
            author=scanned.author_hint,
            identifiers=scanned.identifiers,
            publication_year=scanned.publication_year_hint,
            series=scanned.series_hint,
            series_position=scanned.series_position_hint,
        )
        result = find_match(session, inp)
        if result.level in (MatchLevel.STRONG, MatchLevel.PROBABLE) and result.work_id:
            asset.work_id = result.work_id
        elif result.level == MatchLevel.NEEDS_REVIEW and result.work_id:
            review = ReviewItem(
                asset_id=asset.id,
                candidate_work_id=result.work_id,
                confidence=result.confidence,
                reasons={"reasons": result.reasons, "title": inp.title, "author": inp.author},
            )
            session.add(review)
            stats.review_items_created += 1
        else:
            work = create_work_from_match(session, inp)
            asset.work_id = work.id
            stats.works_created += 1
        session.add(asset)

    session.commit()
    stats.assets_added += 1


def _build_metadata_blob(root: LibraryRoot, scanned: ScannedAsset) -> dict:
    return {
        "library_root_id": root.id,
        "library_root_path": root.path,
        "library_root_kind": root.kind,
        "title_hint": scanned.title_hint,
        "author_hint": scanned.author_hint,
        "series_hint": scanned.series_hint,
        "series_position_hint": scanned.series_position_hint,
        "publication_year_hint": scanned.publication_year_hint,
        "identifiers": scanned.identifiers,
        "extra": scanned.extra,
    }
