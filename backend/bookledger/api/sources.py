from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from bookledger.db import get_session
from bookledger.models import LibraryRoot

router = APIRouter()


@router.get("")
def list_library_roots(session: Session = Depends(get_session)) -> list[LibraryRoot]:
    return list(session.exec(select(LibraryRoot).order_by(LibraryRoot.kind, LibraryRoot.path)))
