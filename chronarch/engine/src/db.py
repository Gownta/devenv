"""The active_runs table, and helpers for the processes it tracks."""

import os
import signal
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS active_runs (
    rundir TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    pid INTEGER NOT NULL,
    pid_start INTEGER,        -- /proc start time, to detect pid reuse
    start_ts REAL NOT NULL,
    kill_ts REAL NOT NULL,
    kill_reason TEXT,         -- set just before we kill it
    owner_pid INTEGER NOT NULL,  -- the engine process waiting on pid
    owner_start INTEGER
);
CREATE INDEX IF NOT EXISTS active_runs_name ON active_runs (name);
"""


@dataclass
class ActiveRun:
    rundir: str
    name: str
    pid: int
    pid_start: Optional[int]
    start_ts: float
    kill_ts: float
    kill_reason: Optional[str]
    owner_pid: int
    owner_start: Optional[int]

    @property
    def alive(self) -> bool:
        return pid_alive(self.pid, self.pid_start)

    @property
    def orphaned(self) -> bool:
        return not pid_alive(self.owner_pid, self.owner_start)


def proc_start(pid: int) -> Optional[int]:
    try:
        with open(f"/proc/{pid}/stat") as f:
            stat = f.read()
    except OSError:
        return None
    # comm (field 2) may contain spaces and parens; starttime is field 22.
    return int(stat.rsplit(")", 1)[1].split()[19])


def pid_alive(pid: int, start: Optional[int]) -> bool:
    now_start = proc_start(pid)
    if now_start is None:
        return False
    if start is not None and now_start != start:
        return False  # reused pid
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


class DB:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), timeout=60, isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    def insert(self, run: ActiveRun) -> None:
        self.conn.execute(
            "INSERT INTO active_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run.rundir,
                run.name,
                run.pid,
                run.pid_start,
                run.start_ts,
                run.kill_ts,
                run.kill_reason,
                run.owner_pid,
                run.owner_start,
            ),
        )

    def runs(self, name: Optional[str] = None) -> List[ActiveRun]:
        if name is None:
            rows = self.conn.execute("SELECT * FROM active_runs ORDER BY start_ts")
        else:
            rows = self.conn.execute("SELECT * FROM active_runs WHERE name = ? ORDER BY start_ts", (name,))
        return [ActiveRun(*row) for row in rows]

    def set_kill_reason(self, rundir: str, reason: str) -> None:
        # First reason wins: a timeout that races a cancel shouldn't overwrite it.
        self.conn.execute(
            "UPDATE active_runs SET kill_reason = ? WHERE rundir = ? AND kill_reason IS NULL",
            (reason, rundir),
        )

    def claim(self, rundir: str) -> Optional[ActiveRun]:
        """Remove a run, returning it iff we were the one to remove it (and so should finalize it)."""
        row = self.conn.execute("DELETE FROM active_runs WHERE rundir = ? RETURNING *", (rundir,)).fetchone()
        return ActiveRun(*row) if row else None


def kill_group(run: ActiveRun, grace_s: float) -> None:
    """SIGTERM the run's process group, then SIGKILL it once the primary exits or grace_s passes."""
    if not run.alive:
        return
    try:
        os.killpg(run.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + grace_s
    while run.alive and time.time() < deadline:
        time.sleep(0.1)
    try:
        os.killpg(run.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
