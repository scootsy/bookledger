# BookLedger

A personal inventory of your books across ebook and audiobook libraries. Tracks
which formats you own for each work, where they live, and what's missing.

This is a self-hosted single-user app intended to run alongside Audiobookshelf,
Calibre / Calibre-Web, Grimoire, Readarr, etc. on a home server (Unraid,
TrueNAS, plain Docker host). It does not download or replace any of those
tools — it aggregates evidence from them.

**Status:** v0.1. Filesystem scanner, matcher, sources/tags/works UI all
working. Audiobookshelf and Calibre adapters still stubbed.

## Read-only by construction

BookLedger never writes to your library or download folders. Three
layers enforce this:

1. The docker-compose example mounts every library/download volume
   with `:ro`. The Linux kernel rejects any write attempt.
2. The scanner code only ever calls read-mode operations
   (`open(path, "rb")`, `zipfile.ZipFile(path, "r")`,
   `mutagen.File(path)` without `save()`). There are no `os.unlink`,
   `os.rename`, `shutil`, or write-mode opens anywhere in the
   scanner module — verifiable with `grep`.
3. BookLedger's own database lives in `/config`, completely separate
   from your library mounts.

If you'd rather not rely on the compose example, you can mount your
libraries however you like — the `:ro` flag on each volume is the only
hard requirement.

## Architecture

```
+------------------+        +------------------+
| Filesystem scan  |        | Audiobookshelf   |
+--------+---------+        +---------+--------+
         |                            |
         +----------+    +------------+
                    v    v
              +-----+----+-----+         +----------------+
              |   Adapters     |-------->| SourceRecord   |
              +-------+--------+         +----------------+
                      |
                      v
              +-------+--------+         +----------------+
              | Matcher        |<------->| Review queue   |
              +-------+--------+         +----------------+
                      |
                      v
              +-------+--------+
              | Work + Asset   |  (canonical)
              +----------------+
```

- **Work** is the canonical book (a story, regardless of edition or format).
- **Asset** is one file or external record that represents a Work in a specific
  format / source.
- **SourceRecord** is the raw payload from a source, kept for debugging and
  re-matching.
- **Review queue** holds ambiguous matches until a human accepts or rejects them.

## Stack

- Python 3.12 + FastAPI + SQLModel
- SQLite (WAL + FTS5 + JSON1) — single file in `/config`
- APScheduler in-process for periodic scans
- SvelteKit 2 (Svelte 5) + Tailwind v4, built static and served by FastAPI
- One Docker image, one container, one port

## Deploying on Unraid

```yaml
services:
  bookledger:
    image: ghcr.io/scootsy/bookledger:latest  # or build locally
    container_name: bookledger
    ports:
      - "8787:8787"
    environment:
      - TZ=America/Denver
    volumes:
      - /mnt/user/appdata/bookledger:/config
      - /mnt/user/data/media/books:/libraries/books:ro
      - /mnt/user/data/media/audiobooks:/libraries/audiobooks:ro
      - /mnt/user/downloads/books:/downloads/books:ro
      - /mnt/user/downloads/audiobooks:/downloads/audiobooks:ro
```

Adjust the volume paths on the host side to match your share layout. The
container-side paths (`/libraries/books`, etc.) are what the app scans; you
configure which ones to use from the **Sources** page in the UI.

To build locally instead of pulling:

```bash
docker compose up -d --build
```

Then open `http://<server-ip>:8787`.

## Development

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
BOOKLEDGER_CONFIG_DIR=./.dev alembic upgrade head
BOOKLEDGER_CONFIG_DIR=./.dev uvicorn bookledger.main:app --reload --port 8787
```

Frontend (separate terminal, proxies `/api` to the backend):

```bash
cd frontend
npm install
npm run dev
```

## What works today

- **Filesystem scanner.** Walks any number of ebook and audiobook roots
  you configure from the UI. Reads embedded ePub metadata (title,
  author, ISBN/ASIN, series, publication year) and audiobook metadata
  via `mutagen` (title, author, narrator, duration, bitrate). Falls
  back to path-based heuristics when files have no tags.
- **Matcher.** Strong match on identifiers (ISBN/ASIN); probable match
  on normalized title + author; fuzzy match (rapidfuzz) for typos and
  variants; ambiguous matches land in a review queue. Audiobook +
  ebook copies of the same work are linked automatically.
- **Library page.** Filter by coverage (complete / missing audiobook /
  missing ebook / etc.), filter by tags (include + exclude), search by
  title or author, paginated.
- **Work detail.** All assets for a work, identifiers, editable tags,
  audience, free-form notes.
- **Tag system.** Twelve sensible defaults seeded on first boot
  (`kids`, `ya`, `comic`, `reference`, `religious`, `textbook`,
  `low-priority`, `wishlist`, `favorite-author`, `ignored`,
  `audiobook-may-not-exist`, `needs-review`). Add/remove your own.
- **Background scans.** Trigger from the dashboard or per-source, poll
  status, see per-root totals once finished.

## What's planned next

1. Audiobookshelf adapter (reads ABS as another source alongside
   filesystem).
2. Calibre adapter (`metadata.db` read-only).
3. Open Library + Audible (Audnexus) lookups so the UI can show
   "audiobook exists upstream" vs "audiobook may not exist".
4. Review queue UX (accept / reject / merge / split).
5. Automated audience detection for picture books.

## What's out of scope

- Downloading or requesting books.
- Replacing Readarr / Audiobookshelf / Calibre.
- Multi-user auth (put it behind Authentik / NPM if you need that).
