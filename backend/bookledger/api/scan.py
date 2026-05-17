from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from bookledger.db import engine, get_session
from bookledger.models import LibraryRoot
from bookledger.services.scan_state import RootResult, scan_state
from bookledger.services.scanner.orchestrator import scan_library_root

logger = logging.getLogger(__name__)
router = APIRouter()

_run_lock = threading.Lock()


def _run_scan(root_ids: list[int] | None) -> None:
    if not scan_state.begin():
        logger.warning("scan already running, skipping")
        return
    try:
        with Session(engine) as session:
            stmt = select(LibraryRoot).where(LibraryRoot.enabled.is_(True))
            if root_ids is not None:
                stmt = stmt.where(LibraryRoot.id.in_(root_ids))
            roots = list(session.exec(stmt))
            for root in roots:
                scan_state.set_current_root(root.id, root.path)
                stats = scan_library_root(session, root)
                scan_state.append_result(
                    RootResult(
                        library_root_id=root.id,
                        path=root.path,
                        kind=root.kind,
                        files_seen=stats.files_seen,
                        assets_added=stats.assets_added,
                        assets_updated=stats.assets_updated,
                        works_created=stats.works_created,
                        review_items_created=stats.review_items_created,
                        errors=stats.errors,
                    )
                )
        scan_state.end()
    except Exception as exc:
        logger.exception("scan failed")
        scan_state.end(error=str(exc))


@router.get("/status")
def get_scan_status() -> dict:
    return scan_state.snapshot()


@router.post("/run", status_code=202)
def trigger_scan_all(
    background: BackgroundTasks,
    session: Session = Depends(get_session),
) -> dict:
    snapshot = scan_state.snapshot()
    if snapshot["running"]:
        raise HTTPException(status_code=409, detail="A scan is already running")
    enabled_count = session.scalar(
        select(LibraryRoot.id).where(LibraryRoot.enabled.is_(True))
    )
    if enabled_count is None:
        raise HTTPException(status_code=400, detail="No enabled sources to scan")
    background.add_task(_run_scan, None)
    return {"status": "started"}


@router.post("/run/{root_id}", status_code=202)
def trigger_scan_one(
    root_id: int,
    background: BackgroundTasks,
    session: Session = Depends(get_session),
) -> dict:
    snapshot = scan_state.snapshot()
    if snapshot["running"]:
        raise HTTPException(status_code=409, detail="A scan is already running")
    root = session.get(LibraryRoot, root_id)
    if not root:
        raise HTTPException(status_code=404, detail="Source not found")
    if not root.enabled:
        raise HTTPException(status_code=400, detail="Source is disabled")
    background.add_task(_run_scan, [root_id])
    return {"status": "started"}
