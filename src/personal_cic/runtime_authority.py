from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import fcntl
import json
import os
from pathlib import Path
from threading import Lock


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkerLifecycle(str, Enum):
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WorkerRuntimeStatus:
    name: str
    lifecycle: WorkerLifecycle
    started_at: str | None
    last_cycle_started_at: str | None
    last_cycle_completed_at: str | None
    stopped_at: str | None
    terminal_failure: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "lifecycle": self.lifecycle.value,
            "started_at": self.started_at,
            "last_cycle_started_at": self.last_cycle_started_at,
            "last_cycle_completed_at": self.last_cycle_completed_at,
            "stopped_at": self.stopped_at,
            "terminal_failure": self.terminal_failure,
        }


class WorkerLiveness:
    """Thread-safe runtime liveness fact for one enabled collection worker.

    This tracker does not confer world authority. It records whether the runtime
    mechanism capable of earning remote observation authority is itself alive.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._lock = Lock()
        self._lifecycle = WorkerLifecycle.INITIALIZED
        self._started_at: str | None = None
        self._last_cycle_started_at: str | None = None
        self._last_cycle_completed_at: str | None = None
        self._stopped_at: str | None = None
        self._terminal_failure: str | None = None

    def _snapshot_unlocked(self) -> WorkerRuntimeStatus:
        return WorkerRuntimeStatus(
            name=self.name,
            lifecycle=self._lifecycle,
            started_at=self._started_at,
            last_cycle_started_at=self._last_cycle_started_at,
            last_cycle_completed_at=self._last_cycle_completed_at,
            stopped_at=self._stopped_at,
            terminal_failure=self._terminal_failure,
        )

    def snapshot(self) -> WorkerRuntimeStatus:
        with self._lock:
            return self._snapshot_unlocked()

    def mark_starting(self) -> WorkerRuntimeStatus:
        with self._lock:
            self._lifecycle = WorkerLifecycle.STARTING
            self._terminal_failure = None
            self._stopped_at = None
            return self._snapshot_unlocked()

    def mark_running(self) -> WorkerRuntimeStatus:
        with self._lock:
            now = _utc_now_iso()
            self._lifecycle = WorkerLifecycle.RUNNING
            if self._started_at is None:
                self._started_at = now
            return self._snapshot_unlocked()

    def mark_cycle_started(self) -> WorkerRuntimeStatus:
        with self._lock:
            self._last_cycle_started_at = _utc_now_iso()
            return self._snapshot_unlocked()

    def mark_cycle_completed(self) -> WorkerRuntimeStatus:
        with self._lock:
            self._last_cycle_completed_at = _utc_now_iso()
            return self._snapshot_unlocked()

    def mark_stopping(self) -> WorkerRuntimeStatus:
        with self._lock:
            if self._lifecycle is not WorkerLifecycle.FAILED:
                self._lifecycle = WorkerLifecycle.STOPPING
            return self._snapshot_unlocked()

    def mark_stopped(self) -> WorkerRuntimeStatus:
        with self._lock:
            if self._lifecycle is not WorkerLifecycle.FAILED:
                self._lifecycle = WorkerLifecycle.STOPPED
                self._stopped_at = _utc_now_iso()
            return self._snapshot_unlocked()

    def mark_failed(self, detail: str) -> WorkerRuntimeStatus:
        detail = " ".join(str(detail).split())[:1000]
        with self._lock:
            self._lifecycle = WorkerLifecycle.FAILED
            self._terminal_failure = detail or "unspecified worker failure"
            self._stopped_at = _utc_now_iso()
            return self._snapshot_unlocked()


class WorkerAuthorityFailure(RuntimeError):
    """An enabled collection worker can no longer earn runtime authority."""


class DurableStateLeaseError(RuntimeError):
    """The durable Personal CIC embodiment is already owned by another writer."""


class DurableStateLease:
    """OS-enforced single-writer lease for one durable WorldState embodiment.

    File existence is not authority: the advisory flock held by this process is.
    The persistent lock file is only a diagnostic record of the latest owner.
    """

    def __init__(self, state_path: Path) -> None:
        # Canonicalize the lock target so relative/symlinked spellings cannot create
        # separate lease files for the same durable embodiment.
        self.state_path = Path(state_path).expanduser().resolve()
        self.path = self.state_path.with_name(self.state_path.name + ".lock")
        self._handle = None

    @property
    def held(self) -> bool:
        return self._handle is not None

    def acquire(self) -> None:
        if self._handle is not None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            handle.seek(0)
            owner = handle.read().strip()
            handle.close()
            detail = f"durable state already leased: {self.state_path}"
            if owner:
                detail += f" // owner record: {owner}"
            raise DurableStateLeaseError(detail) from exc

        record = {
            "pid": os.getpid(),
            "acquired_at": _utc_now_iso(),
            "state_path": str(self.state_path),
        }
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        self._handle = handle

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return
        self._handle = None
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def __enter__(self) -> "DurableStateLease":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.release()
