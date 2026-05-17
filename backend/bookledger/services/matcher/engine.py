from dataclasses import dataclass, field
from enum import Enum


class MatchLevel(str, Enum):
    STRONG = "strong"
    PROBABLE = "probable"
    NEEDS_REVIEW = "needs_review"
    NO_MATCH = "no_match"


@dataclass
class MatchResult:
    level: MatchLevel
    work_id: int | None
    confidence: float
    reasons: list[str] = field(default_factory=list)


def match_record_to_work(*args, **kwargs) -> MatchResult:
    raise NotImplementedError("matcher engine not implemented yet")
