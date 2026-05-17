from dataclasses import dataclass


@dataclass
class OpenLibraryWork:
    olid: str
    title: str
    authors: list[str]
    publish_year: int | None
    isbns: list[str]


def search_work(title: str, author: str) -> list[OpenLibraryWork]:
    raise NotImplementedError("open library lookup not implemented yet")
