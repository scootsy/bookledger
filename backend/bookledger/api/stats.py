from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlmodel import Session

from bookledger.db import get_session
from bookledger.models import Asset, ReviewItem, Tag, Work

router = APIRouter()


@router.get("")
def get_stats(session: Session = Depends(get_session)) -> dict[str, int]:
    return {
        "works": session.scalar(select(func.count()).select_from(Work)) or 0,
        "assets": session.scalar(select(func.count()).select_from(Asset)) or 0,
        "tags": session.scalar(select(func.count()).select_from(Tag)) or 0,
        "review_queue": session.scalar(
            select(func.count()).select_from(ReviewItem).where(ReviewItem.status == "pending")
        ) or 0,
    }
