"""Executing a single cron run."""

import fcntl
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

import rundir as rundirs
from config import Config, Cron
from db import DB, ActiveRun, kill_group, proc_start

log = logging.getLogger("chronarch")


def command(cron: Cron) -> List[str]:
    """The argv to run. AI crons read the .md file on stdin."""
    if cron.provider == "claude":
        cmd = ["claude", "-p"]
        if cron.model:
            cmd += ["--model", cron.model]
        if cron.effort:
            cmd += ["--effort", cron.effort]
        return cmd + cron.ai_args
    if cron.provider == "codex":
        cmd = ["codex", "exec"]
        if cron.model:
            cmd += ["--model", cron.model]
        if cron.effort:
            cmd += ["-c", f'model_reasoning_effort="{cron.effort}"']
        return cmd + cron.ai_args + ["-"]
    return [str(cron.exe)]


def execute(
    cfg: Config,
    cron: Cron,
    on_start: Optional[Callable[[ActiveRun], None]] = None,
    cancel: Optional[threading.Event] = None,
) -> Optional[int]:
    """Run cron to completion, or until cancel is set. Returns its exit code, or None if it didn't start."""
    base = cfg.rundir_base(cron.name)
    base.mkdir(parents=True, exist_ok=True)
    db = DB(cfg.db_path)
    lock = open(base / "_lockfile.flock", "w")
    try:
        # Non-concurrent crons hold the lock for the whole run; concurrent ones only while initiating.
        flags = fcntl.LOCK_EX | (fcntl.LOCK_NB if cron.max_concurrent == 1 else 0)
        try:
            fcntl.flock(lock, flags)
        except BlockingIOError:
            log.info("%s: already running, skipping", cron.name)
            return None

        # The lock dies with its engine process, so also count runs left behind by dead engines.
        running = sum(1 for r in db.runs(cron.name) if r.alive)
        if running >= cron.max_concurrent:
            log.info("%s: %d runs active (max_concurrent=%d), skipping", cron.name, running, cron.max_concurrent)
            return None

        start_ts = time.time()
        rundir = rundirs.create(base, start_ts)
        cmd = command(cron)
        rundirs.append_meta(
            rundir,
            name=cron.name,
            command=cmd if cron.is_ai else None,
            exe=str(cron.exe),
            start_time=rundirs.human_time(start_ts),
            max_duration_s=int(cron.timeout_s) if cron.timeout_s.is_integer() else cron.timeout_s,
        )
        env = {
            **os.environ,
            "CHRONARCH_RUNDIR": str(rundir),
            "CHRONARCH_CRON": cron.name,
            "CHRONARCH_ROOT": str(cfg.root),
        }
        try:
            with open(cron.exe if cron.is_ai else os.devnull, "rb") as stdin, open(
                rundir / "stdout.txt", "wb"
            ) as stdout, open(rundir / "stderr.txt", "wb") as stderr:
                proc = subprocess.Popen(
                    cmd,
                    cwd=cron.root_dir,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=stderr,
                    env=env,
                    start_new_session=True,  # own process group, and survives engine restarts
                )
        except OSError as e:
            log.error("%s: failed to start %s: %s", cron.name, cmd, e)
            rundirs.finish(rundir, start_ts, time.time(), exit_code=127, error=str(e))
            return 127
        rundirs.append_meta(rundir, pid=proc.pid)

        run = ActiveRun(
            rundir=str(rundir),
            name=cron.name,
            pid=proc.pid,
            pid_start=proc_start(proc.pid),
            start_ts=start_ts,
            kill_ts=start_ts + cron.timeout_s,
            kill_reason=None,
            owner_pid=os.getpid(),
            owner_start=proc_start(os.getpid()),
        )
        db.insert(run)
        if cron.max_concurrent != 1:
            fcntl.flock(lock, fcntl.LOCK_UN)
        log.info("%s: started pid %d in %s", cron.name, proc.pid, rundir)
        if on_start:
            on_start(run)

        while proc.poll() is None:
            if cancel and cancel.is_set():
                reason = "cancelled"
            elif time.time() >= run.kill_ts:
                reason = "timeout"
            else:
                try:
                    proc.wait(timeout=min(run.kill_ts - time.time(), 0.2 if cancel else float("inf")))
                except subprocess.TimeoutExpired:
                    pass
                continue
            log.info("%s: killing pid %d (%s)", cron.name, proc.pid, reason)
            db.set_kill_reason(run.rundir, reason)
            kill_group(run, cron.kill_grace_s)
            break
        exit_code = proc.wait()

        end_ts = time.time()
        claimed = db.claim(run.rundir)
        kill_reason = claimed.kill_reason if claimed else None
        if claimed:
            rundirs.finish(rundir, start_ts, end_ts, exit_code=exit_code, kill_reason=kill_reason)
        log.info("%s: pid %d exited %d%s", cron.name, proc.pid, exit_code, f" ({kill_reason})" if kill_reason else "")
        return exit_code
    finally:
        lock.close()
        db.close()


def reap_orphan(db: DB, run: ActiveRun, grace_s: float, now: float) -> None:
    """Handle a run whose engine process died: enforce kill_ts, and finalize it once it exits."""
    if run.alive:
        if now >= run.kill_ts:
            log.info("%s: orphaned pid %d timed out, killing", run.name, run.pid)
            db.set_kill_reason(run.rundir, "timeout")
            kill_group(run, grace_s)
        if run.alive:
            return
    run = db.claim(run.rundir)
    if not run:
        return  # its owner finalized it after all
    # Not our child, so its exit code is lost.
    log.info("%s: orphaned pid %d has exited, finalizing %s", run.name, run.pid, run.rundir)
    rundirs.finish(
        Path(run.rundir),
        run.start_ts,
        time.time(),
        kill_reason=run.kill_reason,
        note="orphaned: engine exited before the run did; end_time is when it was noticed",
    )
