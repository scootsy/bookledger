from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz
from sqlmodel import Session, select

from bookledger.models import Contributor, Work, WorkContributor
from bookledger.services.matcher.normalize import (
    normalize_author,
    normalize_title,
    sort_author,
)


class MatchLevel(str, Enum):
    STRONG = "strong"
    PROBABLE = "probable"
    NEEDS_REVIEW = "needs_review"
    NEW = "new"


@dataclass
class MatchInput:
    title: str
    author: str | None = None
    identifiers: dict[str, str] = field(default_factory=dict)
    publication_year: int | None = None
    series: str | None = None
    series_position: float | None = None


@dataclass
class MatchResult:
    level: MatchLevel
    work_id: int | None
    confidence: float
    reasons: list[str] = field(default_factory=list)


_TITLE_FUZZ_MIN = 0.85
_AUTHOR_FUZZ_MIN = 0.70
_PROBABLE_COMBINED_MIN = 0.92
_REVIEW_COMBINED_MIN = 0.75


def find_match(session: Session, inp: MatchInput) -> MatchResult:
    norm_title = normalize_title(inp.title)
    if not norm_title:
        return MatchResult(MatchLevel.NEW, None, 0.0, ["empty title"])

    if inp.identifiers:
        result = _match_by_identifier(session, inp.identifiers)
        if result is not None:
            return result

    norm_author = normalize_author(inp.author) if inp.author else ""

    exact_title_matches = list(
        session.exec(select(Work).where(Work.normalized_title == norm_title))
    )
    if exact_title_matches:
        if norm_author:
            for w in exact_title_matches:
                authors = _work_normalized_authors(session, w.id)
                if norm_author in authors:
                    return MatchResult(MatchLevel.PROBABLE, w.id, 0.95, ["title+author exact"])
        elif len(exact_title_matches) == 1:
            return MatchResult(
                MatchLevel.PROBABLE,
                exact_title_matches[0].id,
                0.85,
                ["unique normalized title, no author"],
            )

    return _match_fuzzy(session, norm_title, norm_author)


def _match_by_identifier(
    session: Session, identifiers: dict[str, str]
) -> MatchResult | None:
    normalized = {k: v.strip() for k, v in identifiers.items() if v and v.strip()}
    if not normalized:
        return None
    for work in session.exec(select(Work)):
        if not work.identifiers:
            continue
        for scheme, value in normalized.items():
            if work.identifiers.get(scheme) == value:
                return MatchResult(
                    MatchLevel.STRONG,
                    work.id,
                    1.0,
                    [f"identifier match ({scheme})"],
                )
    return None


def _match_fuzzy(session: Session, norm_title: str, norm_author: str) -> MatchResult:
    if norm_author:
        candidates_ids = _candidate_work_ids_by_author(session, norm_author)
        if candidates_ids:
            candidates = [
                w
                for w in (session.get(Work, wid) for wid in candidates_ids)
                if w is not None
            ]
        else:
            candidates = list(session.exec(select(Work)))
    else:
        candidates = list(session.exec(select(Work)))

    best: tuple[Work, float, str] | None = None
    for w in candidates:
        title_score = fuzz.token_sort_ratio(norm_title, w.normalized_title) / 100.0
        if title_score < _TITLE_FUZZ_MIN:
            continue
        if norm_author:
            author_score = 0.0
            for ca in _work_normalized_authors(session, w.id):
                author_score = max(author_score, fuzz.token_sort_ratio(norm_author, ca) / 100.0)
            if author_score < _AUTHOR_FUZZ_MIN:
                continue
            combined = title_score * 0.6 + author_score * 0.4
            reason = f"fuzzy title={title_score:.2f} author={author_score:.2f}"
        else:
            combined = title_score * 0.7
            reason = f"fuzzy title only={title_score:.2f}"
        if best is None or combined > best[1]:
            best = (w, combined, reason)

    if best:
        w, score, reason = best
        if score >= _PROBABLE_COMBINED_MIN:
            return MatchResult(MatchLevel.PROBABLE, w.id, score, [reason])
        if score >= _REVIEW_COMBINED_MIN:
            return MatchResult(MatchLevel.NEEDS_REVIEW, w.id, score, [reason])

    return MatchResult(MatchLevel.NEW, None, 0.0, ["no candidate"])


def _work_normalized_authors(session: Session, work_id: int) -> list[str]:
    rows = session.exec(
        select(Contributor.normalized_name)
        .join(WorkContributor, WorkContributor.contributor_id == Contributor.id)
        .where(WorkContributor.work_id == work_id, WorkContributor.role == "author")
    )
    return list(rows)


def _candidate_work_ids_by_author(session: Session, norm_author: str) -> list[int]:
    tokens = [t for t in norm_author.split() if len(t) >= 2]
    if not tokens:
        return []
    surname = tokens[-1]
    rows = session.exec(
        select(WorkContributor.work_id)
        .join(Contributor, Contributor.id == WorkContributor.contributor_id)
        .where(
            WorkContributor.role == "author",
            Contributor.normalized_name.contains(surname),
        )
        .distinct()
    )
    return list(rows)


def create_work_from_match(session: Session, inp: MatchInput) -> Work:
    norm_title = normalize_title(inp.title)
    primary_author = ""
    author_names: list[str] = []
    if inp.author:
        author_names = [a.strip() for a in inp.author.split(",") if a.strip()]
        if author_names:
            primary_author = author_names[0]

    work = Work(
        title=inp.title,
        normalized_title=norm_title,
        sort_author=sort_author(primary_author) if primary_author else "zzz unknown",
        series=inp.series,
        series_position=inp.series_position,
        publication_year=inp.publication_year,
        identifiers=inp.identifiers,
    )
    session.add(work)
    session.flush()

    for name in author_names:
        _link_author(session, work.id, name)

    return work


def _link_author(session: Session, work_id: int, name: str) -> None:
    norm = normalize_author(name)
    if not norm:
        return
    contributor = session.exec(
        select(Contributor).where(Contributor.normalized_name == norm)
    ).first()
    if not contributor:
        contributor = Contributor(
            name=name,
            normalized_name=norm,
            sort_name=sort_author(name),
        )
        session.add(contributor)
        session.flush()
    existing = session.exec(
        select(WorkContributor).where(
            WorkContributor.work_id == work_id,
            WorkContributor.contributor_id == contributor.id,
            WorkContributor.role == "author",
        )
    ).first()
    if not existing:
        session.add(
            WorkContributor(
                work_id=work_id,
                contributor_id=contributor.id,
                role="author",
            )
        )
