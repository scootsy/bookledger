import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import Tag, WorkTag

router = APIRouter()

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


class TagCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    label: str = Field(min_length=1, max_length=128)
    color: str | None = Field(default=None, max_length=16)
    is_filter: bool = True


class TagUpdate(BaseModel):
    label: str | None = None
    color: str | None = None
    is_filter: bool | None = None


@router.get("")
def list_tags(session: Session = Depends(get_session)) -> list[Tag]:
    return list(session.exec(select(Tag).order_by(Tag.label)))


@router.post("", status_code=201)
def create_tag(payload: TagCreate, session: Session = Depends(get_session)) -> Tag:
    if not _SLUG_RE.match(payload.slug):
        raise HTTPException(
            status_code=400,
            detail="slug must be lowercase, alphanumeric or hyphen, 2+ chars",
        )
    existing = session.exec(select(Tag).where(Tag.slug == payload.slug)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tag already exists")
    tag = Tag(
        slug=payload.slug,
        label=payload.label,
        color=payload.color,
        is_filter=payload.is_filter,
    )
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.patch("/{tag_id}")
def update_tag(
    tag_id: int, payload: TagUpdate, session: Session = Depends(get_session)
) -> Tag:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if payload.label is not None:
        tag.label = payload.label
    if payload.color is not None:
        tag.color = payload.color or None
    if payload.is_filter is not None:
        tag.is_filter = payload.is_filter
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, session: Session = Depends(get_session)) -> None:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    for wt in session.exec(select(WorkTag).where(WorkTag.tag_id == tag_id)).all():
        session.delete(wt)
    session.delete(tag)
    session.commit()
