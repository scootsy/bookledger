from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class RootResult:
    library_root_id: int
    path: str
    kind: str
    files_seen: int = 0
    assets_added: int = 0
    assets_updated: int = 0
    works_created: int = 0
    review_items_created: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class ScanState:
    running: bool = False
    started_at: str | None = None
    finished_at: str | None = None
    current_root_id: int | None = None
    current_root_path: str | None = None
    results: list[RootResult] = field(default_factory=list)
    error: str | None = None


class ScanStateStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = ScanState()

    def snapshot(self) -> dict:
        with self._lock:
            data = asdict(self._state)
            return data

    def begin(self) -> bool:
        with self._lock:
            if self._state.running:
                return False
            self._state = ScanState(
                running=True,
                started_at=datetime.utcnow().isoformat() + "Z",
            )
            return True

    def set_current_root(self, root_id: int, path: str) -> None:
        with self._lock:
            self._state.current_root_id = root_id
            self._state.current_root_path = path

    def append_result(self, result: RootResult) -> None:
        with self._lock:
            self._state.results.append(result)

    def end(self, error: str | None = None) -> None:
        with self._lock:
            self._state.running = False
            self._state.current_root_id = None
            self._state.current_root_path = None
            self._state.finished_at = datetime.utcnow().isoformat() + "Z"
            if error:
                self._state.error = error


scan_state = ScanStateStore()
