from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import Work

router = APIRouter()


@router.get("")
def list_works(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[Work]:
    stmt = select(Work).order_by(Work.sort_author, Work.normalized_title).limit(limit).offset(offset)
    return list(session.exec(stmt))


@router.get("/{work_id}")
def get_work(work_id: int, session: Session = Depends(get_session)) -> Work:
    work = session.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work
