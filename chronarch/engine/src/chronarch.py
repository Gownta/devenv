#!/usr/bin/python3
"""Chronarch: an AI cron engine. See ../../README.md."""

import argparse
import logging
import signal
import sys
import threading

import config as configs
import runner
from config import SpecError
from db import DB, kill_group
from drive import Driver

log = logging.getLogger("chronarch")


def setup_logging(cfg: configs.Config) -> None:
    cfg.root.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(cfg.log_path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(process)d %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def cmd_drive(cfg, args) -> int:
    try:
        Driver(cfg).loop()
    except KeyboardInterrupt:
        log.info("drive stopped; active runs keep going and will be reclaimed on restart")
    return 0


def cmd_run(cfg, args) -> int:
    cron = configs.load_cron(cfg, args.name)
    # Ctrl-C (or SIGTERM) cancels the run rather than abandoning it.
    cancel = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: cancel.set())
    code = runner.execute(cfg, cron, lambda run: print(f"{run.rundir}  pid {run.pid}", flush=True), cancel)
    if code is None:
        print(f"{cron.name}: not started (already running)", file=sys.stderr)
        return 1
    return 128 - code if code < 0 else code  # killed by a signal: shell convention


def cmd_kill(cfg, args) -> int:
    try:
        grace = configs.load_cron(cfg, args.name).kill_grace_s
    except SpecError:
        grace = cfg.raw.get("process", {}).get("kill_grace_s", 10)
    db = DB(cfg.db_path)
    try:
        runs = [r for r in db.runs(args.name) if r.alive]
        if not runs:
            print(f"{args.name}: not running", file=sys.stderr)
            return 1
        for run in runs:
            log.info("%s: cancelling pid %d", run.name, run.pid)
            db.set_kill_reason(run.rundir, "cancelled")
            kill_group(run, grace)
            if run.orphaned:
                runner.reap_orphan(db, run, grace, 0)
            print(f"killed {run.pid}  {run.rundir}")
    finally:
        db.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="rr", description="An AI cron engine.")
    parser.add_argument("--config", help="path to config.toml (default: the one next to engine/)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("drive", help="schedule and run crons, forever").set_defaults(func=cmd_drive)
    run = sub.add_parser("run", help="run a cron now, in the foreground")
    run.add_argument("name")
    run.set_defaults(func=cmd_run)
    kill = sub.add_parser("kill", help="stop a running cron")
    kill.add_argument("name")
    kill.set_defaults(func=cmd_kill)
    args = parser.parse_args()

    try:
        cfg = configs.load_config(args.config)
        setup_logging(cfg)
        return args.func(cfg, args)
    except SpecError as e:
        print(f"chronarch: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
