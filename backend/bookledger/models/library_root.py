from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class LibraryRoot(SQLModel, table=True):
    __tablename__ = "library_roots"

    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str
    path: str = Field(unique=True)
    enabled: bool = True
    last_scanned_at: Optional[datetime] = None
