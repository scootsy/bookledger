"""Embedded metadata extraction. Read-only: never modifies the source file."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf",
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
}

_ISBN_RE = re.compile(r"\b(?:97[89])?\d{9}[\dXx]\b")
_ASIN_RE = re.compile(r"\bB[0-9A-Z]{9}\b")


def _detect_identifier_scheme(value: str) -> str | None:
    v = value.strip()
    v_upper = v.upper()
    if v_upper.startswith("URN:ISBN:"):
        return "isbn"
    if v_upper.startswith("ISBN:"):
        return "isbn"
    digits = re.sub(r"[-\s]", "", v)
    if _ISBN_RE.fullmatch(digits):
        return "isbn"
    if _ASIN_RE.fullmatch(v_upper):
        return "asin"
    return None


def _clean_identifier_value(scheme: str, value: str) -> str:
    v = value.strip()
    if scheme == "isbn":
        v = re.sub(r"[-\s]", "", v)
        if v.upper().startswith("URN:ISBN:"):
            v = v[9:]
        elif v.upper().startswith("ISBN:"):
            v = v[5:]
    return v.strip()


def read_epub_metadata(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        with zipfile.ZipFile(path, "r") as z:
            try:
                with z.open("META-INF/container.xml") as cx:
                    container = ET.parse(cx).getroot()
            except KeyError:
                return out
            rootfile = container.find(".//container:rootfile", _NS)
            if rootfile is None:
                return out
            opf_path = rootfile.get("full-path")
            if not opf_path:
                return out
            try:
                with z.open(opf_path) as op:
                    opf = ET.parse(op).getroot()
            except KeyError:
                return out

            metadata = opf.find("opf:metadata", _NS)
            if metadata is None:
                return out

            title_el = metadata.find("dc:title", _NS)
            if title_el is not None and title_el.text:
                out["title"] = title_el.text.strip()

            creators = [
                el.text.strip()
                for el in metadata.findall("dc:creator", _NS)
                if el.text
            ]
            if creators:
                out["authors"] = creators

            identifiers: dict[str, str] = {}
            for ident in metadata.findall("dc:identifier", _NS):
                if not ident.text:
                    continue
                raw_value = ident.text.strip()
                scheme = ident.get("{http://www.idpf.org/2007/opf}scheme", "").lower().strip()
                if not scheme:
                    scheme = _detect_identifier_scheme(raw_value) or ""
                if scheme:
                    identifiers[scheme] = _clean_identifier_value(scheme, raw_value)
            if identifiers:
                out["identifiers"] = identifiers

            date_el = metadata.find("dc:date", _NS)
            if date_el is not None and date_el.text:
                m = re.match(r"(\d{4})", date_el.text.strip())
                if m:
                    year = int(m.group(1))
                    if 1500 <= year <= 2100:
                        out["publication_year"] = year

            pub_el = metadata.find("dc:publisher", _NS)
            if pub_el is not None and pub_el.text:
                out["publisher"] = pub_el.text.strip()

            lang_el = metadata.find("dc:language", _NS)
            if lang_el is not None and lang_el.text:
                out["language"] = lang_el.text.strip()

            for meta_el in metadata.findall("opf:meta", _NS):
                name = meta_el.get("name", "").lower()
                content = meta_el.get("content")
                if name == "calibre:series" and content:
                    out["series"] = content.strip()
                elif name == "calibre:series_index" and content:
                    try:
                        out["series_position"] = float(content)
                    except ValueError:
                        pass
    except (zipfile.BadZipFile, ET.ParseError, OSError, UnicodeDecodeError):
        pass
    return out


def _first_tag_value(tags, *keys: str) -> str | None:
    if not tags:
        return None
    for k in keys:
        try:
            v = tags.get(k) if hasattr(tags, "get") else tags[k]
        except (KeyError, ValueError):
            continue
        if v is None:
            continue
        if isinstance(v, list):
            if not v:
                continue
            v = v[0]
        s = str(v).strip()
        if s:
            return s
    return None


def read_audio_metadata(path: Path) -> dict[str, Any]:
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return {}
    try:
        m = MutagenFile(path)
    except Exception:
        return {}
    if m is None:
        return {}

    out: dict[str, Any] = {}
    info = getattr(m, "info", None)
    if info is not None:
        length = getattr(info, "length", None)
        if isinstance(length, (int, float)) and length > 0:
            out["duration_seconds"] = int(length)
        bitrate = getattr(info, "bitrate", None)
        if isinstance(bitrate, int) and bitrate > 0:
            out["bitrate"] = bitrate

    tags = m.tags
    title = _first_tag_value(tags, "\xa9nam", "TIT2", "title", "TITLE", "Title")
    if title:
        out["title"] = title
    album = _first_tag_value(tags, "\xa9alb", "TALB", "album", "ALBUM", "Album")
    if album:
        out["album"] = album
    author = _first_tag_value(
        tags, "\xa9ART", "TPE1", "artist", "ARTIST", "Artist", "author", "AUTHOR"
    )
    if author:
        out["author"] = author
    narrator = _first_tag_value(
        tags, "narrator", "NARRATOR", "Narrator", "\xa9wrt", "TCOM", "composer", "COMPOSER"
    )
    if narrator and narrator != author:
        out["narrator"] = narrator
    return out
