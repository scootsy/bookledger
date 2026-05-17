from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class SourceRecord(SQLModel, table=True):
    __tablename__ = "source_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_kind: str = Field(index=True)
    source_id: str = Field(index=True)
    raw: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
