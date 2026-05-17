# BookLedger

A personal inventory of your books across ebook and audiobook libraries. Tracks
which formats you own for each work, where they live, and what's missing.

This is a self-hosted single-user app intended to run alongside Audiobookshelf,
Calibre / Calibre-Web, Grimoire, Readarr, etc. on a home server (Unraid,
TrueNAS, plain Docker host). It does not download or replace any of those
tools — it aggregates evidence from them.

**Status:** v0.1 scaffold. Schema, container layout, and UI shell are in
place; adapters and matching are stubbed.

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

## What's planned next

1. Filesystem scanner (epub/mobi/azw3/pdf + m4b/mp3 with embedded metadata).
2. Audiobookshelf adapter.
3. Calibre adapter (reads `metadata.db` read-only).
4. Matcher: identifier → fuzzy title+author → review queue.
5. Open Library + Audible (Audnexus) lookups to answer "does an audiobook
   even exist?"
6. Dashboard with coverage badges, missing-format reports, tag filters.

## What's out of scope

- Downloading or requesting books.
- Replacing Readarr / Audiobookshelf / Calibre.
- Multi-user auth (put it behind Authentik / NPM if you need that).
