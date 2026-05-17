from typing import Optional

from sqlmodel import Field, SQLModel


class Contributor(SQLModel, table=True):
    __tablename__ = "contributors"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    normalized_name: str = Field(index=True)
    sort_name: str = Field(index=True)


class WorkContributor(SQLModel, table=True):
    __tablename__ = "work_contributors"

    work_id: int = Field(foreign_key="works.id", primary_key=True)
    contributor_id: int = Field(foreign_key="contributors.id", primary_key=True)
    role: str = Field(primary_key=True)
    position: int = 0
