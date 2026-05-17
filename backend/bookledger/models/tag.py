from typing import Optional

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    label: str
    color: Optional[str] = None
    is_filter: bool = True


class WorkTag(SQLModel, table=True):
    __tablename__ = "work_tags"

    work_id: int = Field(foreign_key="works.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)
