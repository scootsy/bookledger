from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Asset(SQLModel, table=True):
    __tablename__ = "assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    work_id: Optional[int] = Field(default=None, foreign_key="works.id", index=True)
    type: str = Field(index=True)
    format: Optional[str] = None
    source_kind: str = Field(index=True)
    source_id: Optional[str] = Field(default=None, index=True)
    path: Optional[str] = None
    content_hash: Optional[str] = Field(default=None, index=True)
    size_bytes: Optional[int] = None
    duration_seconds: Optional[int] = None
    page_count: Optional[int] = None
    bitrate: Optional[int] = None
    narrator: Optional[str] = None
    abridged: Optional[bool] = None
    metadata_blob: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
