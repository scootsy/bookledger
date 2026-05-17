from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import (
    Asset,
    Contributor,
    Tag,
    Work,
    WorkContributor,
    WorkTag,
)

router = APIRouter()


class TagView(BaseModel):
    id: int
    slug: str
    label: str
    color: str | None


class WorkListItem(BaseModel):
    id: int
    title: str
    sort_author: str
    series: str | None
    series_position: float | None
    publication_year: int | None
    audience: str | None
    ebook_count: int
    audiobook_count: int
    authors: list[str]
    tags: list[TagView]


class AssetView(BaseModel):
    id: int
    type: str
    format: str | None
    path: str | None
    source_kind: str
    size_bytes: int | None
    duration_seconds: int | None
    page_count: int | None
    bitrate: int | None
    narrator: str | None
    metadata_blob: dict
    first_seen: datetime
    last_seen: datetime


class WorkDetail(BaseModel):
    id: int
    title: str
    normalized_title: str
    sort_author: str
    authors: list[str]
    series: str | None
    series_position: float | None
    publication_year: int | None
    audience: str | None
    identifiers: dict
    notes: str | None
    tags: list[TagView]
    assets: list[AssetView]


CoverageFilter = Literal["all", "has_ebook", "has_audiobook", "complete", "missing_ebook", "missing_audiobook", "orphan"]


@router.get("")
def list_works(
    q: str | None = None,
    coverage: CoverageFilter = "all",
    tag: list[str] | None = Query(default=None),
    exclude_tag: list[str] | None = Query(default=None),
    audience: list[str] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> dict:
    ebook_count_expr = func.count(
        case((Asset.type == "ebook", Asset.id), else_=None)
    ).label("ebook_count")
    audiobook_count_expr = func.count(
        case((Asset.type == "audiobook", Asset.id), else_=None)
    ).label("audiobook_count")

    base = (
        select(
            Work.id,
            Work.title,
            Work.sort_author,
            Work.series,
            Work.series_position,
            Work.publication_year,
            Work.audience,
            ebook_count_expr,
            audiobook_count_expr,
        )
        .outerjoin(Asset, Asset.work_id == Work.id)
        .group_by(Work.id)
        .order_by(Work.sort_author, Work.normalized_title)
    )

    if q:
        like = f"%{q.lower()}%"
        author_subq = (
            select(WorkContributor.work_id)
            .join(Contributor, Contributor.id == WorkContributor.contributor_id)
            .where(func.lower(Contributor.name).like(like))
        )
        base = base.where(
            (func.lower(Work.title).like(like))
            | (func.lower(Work.sort_author).like(like))
            | (Work.id.in_(author_subq))
        )

    if audience:
        base = base.where(Work.audience.in_(audience))

    if tag:
        for t_slug in tag:
            sub = (
                select(WorkTag.work_id)
                .join(Tag, Tag.id == WorkTag.tag_id)
                .where(Tag.slug == t_slug)
            )
            base = base.where(Work.id.in_(sub))

    if exclude_tag:
        for t_slug in exclude_tag:
            sub = (
                select(WorkTag.work_id)
                .join(Tag, Tag.id == WorkTag.tag_id)
                .where(Tag.slug == t_slug)
            )
            base = base.where(~Work.id.in_(sub))

    if coverage == "has_ebook":
        base = base.having(ebook_count_expr > 0)
    elif coverage == "has_audiobook":
        base = base.having(audiobook_count_expr > 0)
    elif coverage == "complete":
        base = base.having(ebook_count_expr > 0).having(audiobook_count_expr > 0)
    elif coverage == "missing_ebook":
        base = base.having(ebook_count_expr == 0).having(audiobook_count_expr > 0)
    elif coverage == "missing_audiobook":
        base = base.having(audiobook_count_expr == 0).having(ebook_count_expr > 0)
    elif coverage == "orphan":
        base = base.having(ebook_count_expr == 0).having(audiobook_count_expr == 0)

    total_subq = base.subquery()
    total = session.scalar(select(func.count()).select_from(total_subq))

    rows = session.exec(base.limit(limit).offset(offset)).all()
    work_ids = [r.id for r in rows]

    authors_by_work = _authors_for_works(session, work_ids)
    tags_by_work = _tags_for_works(session, work_ids)

    items = [
        WorkListItem(
            id=r.id,
            title=r.title,
            sort_author=r.sort_author,
            series=r.series,
            series_position=r.series_position,
            publication_year=r.publication_year,
            audience=r.audience,
            ebook_count=r.ebook_count,
            audiobook_count=r.audiobook_count,
            authors=authors_by_work.get(r.id, []),
            tags=tags_by_work.get(r.id, []),
        )
        for r in rows
    ]
    return {"total": total or 0, "limit": limit, "offset": offset, "items": items}


@router.get("/{work_id}")
def get_work(work_id: int, session: Session = Depends(get_session)) -> WorkDetail:
    work = session.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    authors = _authors_for_works(session, [work_id]).get(work_id, [])
    tags = _tags_for_works(session, [work_id]).get(work_id, [])
    assets_rows = session.exec(
        select(Asset).where(Asset.work_id == work_id).order_by(Asset.type, Asset.first_seen)
    ).all()
    assets = [
        AssetView(
            id=a.id,
            type=a.type,
            format=a.format,
            path=a.path,
            source_kind=a.source_kind,
            size_bytes=a.size_bytes,
            duration_seconds=a.duration_seconds,
            page_count=a.page_count,
            bitrate=a.bitrate,
            narrator=a.narrator,
            metadata_blob=a.metadata_blob,
            first_seen=a.first_seen,
            last_seen=a.last_seen,
        )
        for a in assets_rows
    ]

    return WorkDetail(
        id=work.id,
        title=work.title,
        normalized_title=work.normalized_title,
        sort_author=work.sort_author,
        authors=authors,
        series=work.series,
        series_position=work.series_position,
        publication_year=work.publication_year,
        audience=work.audience,
        identifiers=work.identifiers,
        notes=work.notes,
        tags=tags,
        assets=assets,
    )


class WorkPatch(BaseModel):
    audience: str | None = None
    notes: str | None = None
    tag_slugs: list[str] | None = None


@router.patch("/{work_id}")
def update_work(
    work_id: int,
    payload: WorkPatch,
    session: Session = Depends(get_session),
) -> WorkDetail:
    work = session.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    if payload.audience is not None:
        work.audience = payload.audience or None
    if payload.notes is not None:
        work.notes = payload.notes or None
    work.updated_at = datetime.utcnow()
    session.add(work)

    if payload.tag_slugs is not None:
        for wt in session.exec(select(WorkTag).where(WorkTag.work_id == work_id)).all():
            session.delete(wt)
        if payload.tag_slugs:
            tags = session.exec(select(Tag).where(Tag.slug.in_(payload.tag_slugs))).all()
            for t in tags:
                session.add(WorkTag(work_id=work_id, tag_id=t.id))

    session.commit()
    return get_work(work_id, session)


def _authors_for_works(session: Session, work_ids: list[int]) -> dict[int, list[str]]:
    if not work_ids:
        return {}
    rows = session.exec(
        select(WorkContributor.work_id, Contributor.name)
        .join(Contributor, Contributor.id == WorkContributor.contributor_id)
        .where(
            WorkContributor.role == "author",
            WorkContributor.work_id.in_(work_ids),
        )
        .order_by(WorkContributor.work_id, WorkContributor.position)
    ).all()
    out: dict[int, list[str]] = {}
    for work_id, name in rows:
        out.setdefault(work_id, []).append(name)
    return out


def _tags_for_works(session: Session, work_ids: list[int]) -> dict[int, list[TagView]]:
    if not work_ids:
        return {}
    rows = session.exec(
        select(WorkTag.work_id, Tag.id, Tag.slug, Tag.label, Tag.color)
        .join(Tag, Tag.id == WorkTag.tag_id)
        .where(WorkTag.work_id.in_(work_ids))
        .order_by(Tag.label)
    ).all()
    out: dict[int, list[TagView]] = {}
    for work_id, tag_id, slug, label, color in rows:
        out.setdefault(work_id, []).append(
            TagView(id=tag_id, slug=slug, label=label, color=color)
        )
    return out
