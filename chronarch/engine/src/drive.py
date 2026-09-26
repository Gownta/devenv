"""The scheduler loop."""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set

import config as configs
import runner
from config import Config, Cron, SpecError
from db import DB
from schedule import next_fire

log = logging.getLogger("chronarch")


@dataclass
class Scheduled:
    cron: Cron
    next_ts: Optional[float]


def _launch(cfg: Config, cron: Cron) -> None:
    def on_start(run):
        stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(run.start_ts))
        print(f"{stamp}  {cron.name}  {run.pid}", flush=True)

    def target():
        try:
            runner.execute(cfg, cron, on_start)
        except Exception:
            log.exception("%s: run failed", cron.name)

    threading.Thread(target=target, name=cron.name, daemon=True).start()


class Driver:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.scheduled: Dict[str, Scheduled] = {}
        # The error for each cron that failed to load, so each is only logged once.
        self.bad: Dict[str, str] = {}
        self.nested_errors: Set[str] = set()

    def rescan(self, now: float) -> None:
        names, errors = configs.discover(self.cfg)
        for error in set(errors) - self.nested_errors:
            log.error("%s", error)
        self.nested_errors = set(errors)
        names = set(names)
        for name in list(self.scheduled):
            if name not in names:
                log.info("%s: removed", name)
                del self.scheduled[name]
        for name in sorted(names):
            try:
                cron = configs.load_cron(self.cfg, name)
            except SpecError as e:
                self._bad(name, str(e))
                continue
            old = self.scheduled.get(name)
            if old and old.cron.fingerprint == cron.fingerprint:
                continue
            try:
                next_ts = next_fire(cron.schedules, now)
            except SpecError as e:
                self._bad(name, f"{name}: {e}")
                continue
            self.bad.pop(name, None)
            log.info("%s: %s, next at %s", "updated" if old else "loaded", name, _fmt(next_ts))
            self.scheduled[name] = Scheduled(cron, next_ts)

    def _bad(self, name: str, error: str) -> None:
        if self.bad.get(name) != error:
            log.error("%s", error)
            self.bad[name] = error
        self.scheduled.pop(name, None)

    def boot_report(self) -> None:
        """Print every cron, its schedules, and when it next runs."""
        lines = [
            f"drive started; root {self.cfg.root}",
            f"  specdirs {':'.join(map(str, self.cfg.spec_dirs))}",
        ]
        width = max(map(len, [*self.scheduled, *self.bad]), default=0)
        for name in sorted([*self.scheduled, *self.bad]):
            entry = self.scheduled.get(name)
            if entry:
                schedules = ", ".join(entry.cron.schedules)
                lines.append(f"  {name:{width}}  next {_fmt(entry.next_ts)}  [{schedules}]  {entry.cron.spec_root}")
            else:
                error = self.bad[name]
                error = error[len(name) + 2 :] if error.startswith(f"{name}: ") else error
                lines.append(f"  {name:{width}}  ERROR {error}")
        if width == 0:
            lines.append("  (no crons)")
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{stamp}  " + "\n".join(lines), flush=True)
        for line in lines:
            log.info("%s", line)

    def sweep(self, now: float) -> None:
        """Finalize or kill runs whose engine process is gone."""
        db = DB(self.cfg.db_path)
        try:
            for run in db.runs():
                if not run.orphaned:
                    continue
                entry = self.scheduled.get(run.name)
                grace = entry.cron.kill_grace_s if entry else self.cfg.raw.get("process", {}).get("kill_grace_s", 10)
                try:
                    runner.reap_orphan(db, run, grace, now)
                except Exception:
                    log.exception("%s: failed to reap %s", run.name, run.rundir)
        finally:
            db.close()

    def loop(self) -> None:
        self.rescan(time.time())
        self.boot_report()
        next_sweep = 0.0
        while True:
            now = time.time()
            if now >= next_sweep:
                self.rescan(now)
                self.sweep(now)
                next_sweep = now + self.cfg.sweep_interval_s
            for entry in self.scheduled.values():
                if entry.next_ts is None or entry.next_ts > now:
                    continue
                if now - entry.next_ts > 60:
                    log.warning("%s: missed %s (engine was behind); skipping", entry.cron.name, _fmt(entry.next_ts))
                else:
                    _launch(self.cfg, entry.cron)
                try:
                    entry.next_ts = next_fire(entry.cron.schedules, max(entry.next_ts, now))
                except SpecError as e:
                    log.error("%s: %s", entry.cron.name, e)
                    entry.next_ts = None
            wake = min([next_sweep] + [e.next_ts for e in self.scheduled.values() if e.next_ts is not None])
            time.sleep(max(0.0, min(wake - time.time(), self.cfg.sweep_interval_s)))


def _fmt(ts: Optional[float]) -> str:
    return "never" if ts is None else time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(ts))
