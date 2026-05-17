from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Work(SQLModel, table=True):
    __tablename__ = "works"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    normalized_title: str = Field(index=True)
    sort_author: str = Field(index=True)
    series: Optional[str] = Field(default=None, index=True)
    series_position: Optional[float] = None
    publication_year: Optional[int] = None
    audience: Optional[str] = Field(default=None, index=True)
    identifiers: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
