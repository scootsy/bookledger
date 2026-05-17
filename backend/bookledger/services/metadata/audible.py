from dataclasses import dataclass


@dataclass
class AudibleEdition:
    asin: str
    title: str
    authors: list[str]
    narrators: list[str]
    duration_seconds: int | None
    abridged: bool


def search_audiobook(title: str, author: str) -> list[AudibleEdition]:
    raise NotImplementedError("audible/audnexus lookup not implemented yet")


def audiobook_exists(title: str, author: str) -> bool | None:
    raise NotImplementedError("audiobook existence check not implemented yet")
