from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import Tag

router = APIRouter()


@router.get("")
def list_tags(session: Session = Depends(get_session)) -> list[Tag]:
    return list(session.exec(select(Tag).order_by(Tag.label)))
