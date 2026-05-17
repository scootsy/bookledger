from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import LibraryRoot

router = APIRouter()


class LibraryRootCreate(BaseModel):
    kind: Literal["ebook", "audiobook"]
    path: str = Field(min_length=1)
    enabled: bool = True


class LibraryRootUpdate(BaseModel):
    kind: Literal["ebook", "audiobook"] | None = None
    path: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class LibraryRootView(BaseModel):
    id: int
    kind: str
    path: str
    enabled: bool
    last_scanned_at: datetime | None
    path_exists: bool
    path_is_directory: bool


def _to_view(root: LibraryRoot) -> LibraryRootView:
    p = Path(root.path)
    exists = False
    is_dir = False
    try:
        exists = p.exists()
        is_dir = p.is_dir() if exists else False
    except OSError:
        pass
    return LibraryRootView(
        id=root.id,
        kind=root.kind,
        path=root.path,
        enabled=root.enabled,
        last_scanned_at=root.last_scanned_at,
        path_exists=exists,
        path_is_directory=is_dir,
    )


@router.get("")
def list_sources(session: Session = Depends(get_session)) -> list[LibraryRootView]:
    roots = session.exec(
        select(LibraryRoot).order_by(LibraryRoot.kind, LibraryRoot.path)
    ).all()
    return [_to_view(r) for r in roots]


@router.post("", status_code=201)
def create_source(
    payload: LibraryRootCreate, session: Session = Depends(get_session)
) -> LibraryRootView:
    existing = session.exec(
        select(LibraryRoot).where(LibraryRoot.path == payload.path)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Path already configured")
    root = LibraryRoot(kind=payload.kind, path=payload.path, enabled=payload.enabled)
    session.add(root)
    session.commit()
    session.refresh(root)
    return _to_view(root)


@router.patch("/{root_id}")
def update_source(
    root_id: int,
    payload: LibraryRootUpdate,
    session: Session = Depends(get_session),
) -> LibraryRootView:
    root = session.get(LibraryRoot, root_id)
    if not root:
        raise HTTPException(status_code=404, detail="Source not found")
    if payload.kind is not None:
        root.kind = payload.kind
    if payload.path is not None:
        if payload.path != root.path:
            clash = session.exec(
                select(LibraryRoot).where(LibraryRoot.path == payload.path)
            ).first()
            if clash:
                raise HTTPException(status_code=409, detail="Path already configured")
        root.path = payload.path
    if payload.enabled is not None:
        root.enabled = payload.enabled
    session.add(root)
    session.commit()
    session.refresh(root)
    return _to_view(root)


@router.delete("/{root_id}", status_code=204)
def delete_source(root_id: int, session: Session = Depends(get_session)) -> None:
    root = session.get(LibraryRoot, root_id)
    if not root:
        raise HTTPException(status_code=404, detail="Source not found")
    session.delete(root)
    session.commit()
