from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import ReviewItem

router = APIRouter()


@router.get("")
def list_review_items(
    status: str = "pending",
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[ReviewItem]:
    stmt = (
        select(ReviewItem)
        .where(ReviewItem.status == status)
        .order_by(ReviewItem.confidence.desc(), ReviewItem.created_at)
        .limit(limit)
        .offset(offset)
    )
    return list(session.exec(stmt))
