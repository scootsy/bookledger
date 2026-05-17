import re
import unicodedata

_LEADING_ARTICLES = ("the ", "a ", "an ")
_PUNCTUATION = re.compile(r"[^\w\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower().strip()
    for article in _LEADING_ARTICLES:
        if s.startswith(article):
            s = s[len(article):]
            break
    s = _PUNCTUATION.sub(" ", s)
    s = _WHITESPACE.sub(" ", s).strip()
    return s


def normalize_author(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()
    s = _PUNCTUATION.sub(" ", s)
    s = _WHITESPACE.sub(" ", s).strip()
    return s


def sort_author(name: str) -> str:
    parts = name.strip().rsplit(" ", 1)
    if len(parts) == 2 and "," not in name:
        return f"{parts[1]}, {parts[0]}".lower()
    return name.lower()
