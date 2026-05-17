from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from bookledger.api import review, scan, sources, stats, tags, works
from bookledger.db import engine
from bookledger.services.seed import seed_default_tags


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with Session(engine) as session:
        seed_default_tags(session)
    yield


app = FastAPI(title="BookLedger", version="0.1.0", lifespan=lifespan)


@app.get("/api/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(works.router, prefix="/api/works", tags=["works"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(scan.router, prefix="/api/scan", tags=["scan"])


_frontend_dir = Path(__file__).parent / "static"

if _frontend_dir.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        target = _frontend_dir / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        return FileResponse(_frontend_dir / "index.html")
