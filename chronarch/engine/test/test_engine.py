"""End-to-end tests that drive ./rr against a temporary spec dir and root."""

import os
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

try:
    import tomllib
except ImportError:  # python < 3.11
    import tomli as tomllib

RR = str(Path(__file__).resolve().parents[2] / "rr")


def process_exists(pid: int) -> bool:
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.root = self.dir / "root"
        (self.dir / "config.toml").write_text(
            f'root = "{self.root}"\nspec_dir = "spec"\nsweep_interval_s = 1\n'
            "[process]\ntimeout_s = 60\nkill_grace_s = 1\n"
        )
        self.env = {k: v for k, v in os.environ.items() if k not in ("CHRONARCH_ROOT", "CHRONARCH_SPECDIRS")}
        self.bg = []

    def tearDown(self):
        for p in self.bg:
            if p.poll() is None:
                p.kill()
            p.wait()
            p.stdout.close()
        self.tmp.cleanup()

    def cron(self, name, script, info="", spec_dir="spec"):
        d = self.dir / spec_dir / name
        d.mkdir(parents=True)
        (d / "info.toml").write_text(f'description = "test"\nschedule = "yearly"\nexe = "run.sh"\n{info}')
        (d / "run.sh").write_text(f"#!/bin/bash\n{script}\n")
        (d / "run.sh").chmod(0o755)

    def rr(self, *args, **kwargs):
        return subprocess.run([RR, "--config", str(self.dir / "config.toml"), *args], env=self.env, **kwargs)

    def rr_bg(self, *args):
        proc = subprocess.Popen(
            [RR, "--config", str(self.dir / "config.toml"), *args],
            env=self.env,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.bg.append(proc)
        return proc

    def runs(self, name):
        return sorted((self.root / "rundirs" / name / "runs").iterdir())

    def meta(self, rundir):
        return tomllib.loads((rundir / "meta.toml").read_text())

    def active_rows(self):
        import sqlite3

        return sqlite3.connect(str(self.root / "db")).execute("SELECT name FROM active_runs").fetchall()

    def wait_for(self, predicate, timeout=10):
        deadline = time.time() + timeout
        while not predicate():
            if time.time() > deadline:
                self.fail("timed out waiting")
            time.sleep(0.05)

    def orphan(self, name):
        """Start a run, then SIGKILL the engine process waiting on it."""
        owner = self.rr_bg("run", name)
        pid = int(owner.stdout.readline().split()[-1])
        owner.kill()
        owner.wait()
        self.assertTrue(process_exists(pid))
        return pid


class TestRun(EngineTest):
    def test_success(self):
        self.cron(
            "a/b",
            'echo "$CHRONARCH_CRON $PWD $CHRONARCH_RUNDIR"; echo oops >&2; exit 3',
            '[process]\nroot_dir = "/tmp"\n',
        )
        proc = self.rr("run", "a/b", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3)
        [rundir] = self.runs("a/b")
        self.assertRegex(rundir.name, r"^\d{4}_\d\d_\d\d__\d\d_\d\d_\d\d__0$")
        self.assertEqual((self.root / "rundirs/a/b/latest").resolve(), rundir)
        self.assertEqual((rundir / "stdout.txt").read_text(), f"a/b /tmp {rundir}\n")
        self.assertEqual((rundir / "stderr.txt").read_text(), "oops\n")
        meta = self.meta(rundir)
        self.assertEqual(meta["exit_code"], 3)
        self.assertEqual(meta["max_duration_s"], 60)
        self.assertEqual(meta["duration"], "1s")
        self.assertNotIn("kill_reason", meta)
        self.assertTrue({"start_time", "end_time", "duration_s", "pid"} <= meta.keys())
        self.assertEqual(self.active_rows(), [])

    def test_specdirs(self):
        for spec_dir in ["spec", "env", "flag"]:
            self.cron(f"{spec_dir}_only", "true", spec_dir=spec_dir)
        self.cron("shared", "exit 1")
        self.cron("shared", "exit 3", spec_dir="flag")
        self.env["CHRONARCH_SPECDIRS"] = str(self.dir / "env")
        flag = ["--specdir", str(self.dir / "flag")]
        for args, name, code in [
            ([], "env_only", 0),
            ([], "flag_only", 2),
            (flag, "flag_only", 0),
            (flag, "spec_only", 0),
            (flag, "shared", 1),
            (flag + ["--no-local-specdir"], "spec_only", 2),
            (flag + ["--no-local-specdir"], "shared", 3),
        ]:
            with self.subTest(args=args, name=name):
                self.assertEqual(self.rr(*args, "run", name, capture_output=True).returncode, code)

    def test_not_executable(self):
        self.cron("a", "true")
        (self.dir / "spec/a/run.sh").chmod(0o644)
        self.assertEqual(self.rr("run", "a", capture_output=True).returncode, 127)
        meta = self.meta(self.runs("a")[0])
        self.assertEqual(meta["exit_code"], 127)
        self.assertIn("Permission denied", meta["error"])

    def test_unknown_cron(self):
        self.assertEqual(self.rr("run", "nope", capture_output=True).returncode, 2)

    def test_timeout_kills_group(self):
        self.cron("slow", "sleep 100 & echo $! > sleeper; wait", "[process]\ntimeout_s = 1\n")
        self.assertEqual(self.rr("run", "slow", capture_output=True).returncode, 128 + signal.SIGTERM)
        [rundir] = self.runs("slow")
        meta = self.meta(rundir)
        self.assertEqual((meta["exit_code"], meta["kill_reason"]), (-signal.SIGTERM, "timeout"))
        self.assertGreaterEqual(meta["duration_s"], 1)
        sleeper = int((self.dir / "spec/slow/sleeper").read_text())
        self.assertFalse(process_exists(sleeper))

    def test_not_concurrent(self):
        self.cron("a", "sleep 30")
        first = self.rr_bg("run", "a")
        first.stdout.readline()  # started
        second = self.rr("run", "a", capture_output=True, text=True)
        self.assertEqual(second.returncode, 1)
        self.assertIn("not started", second.stderr)
        self.rr("kill", "a", capture_output=True)
        first.wait()

    def test_max_concurrent(self):
        self.cron("a", "sleep 30", "[process]\nmax_concurrent = 2\n")
        procs = [self.rr_bg("run", "a") for _ in range(2)]
        for p in procs:
            p.stdout.readline()
        self.assertEqual(self.rr("run", "a", capture_output=True).returncode, 1)
        self.assertEqual(len(self.runs("a")), 2)
        self.rr("kill", "a", capture_output=True)
        for p in procs:
            p.wait()


class TestKill(EngineTest):
    def test_kill(self):
        self.cron("a", 'trap "exit 7" TERM; sleep 30 & wait')
        owner = self.rr_bg("run", "a")
        owner.stdout.readline()
        self.assertEqual(self.rr("kill", "a", capture_output=True).returncode, 0)
        self.assertEqual(owner.wait(), 7)
        [rundir] = self.runs("a")
        text = (rundir / "meta.toml").read_text()
        self.assertEqual(text.count("end_time"), 1)
        meta = tomllib.loads(text)
        self.assertEqual((meta["exit_code"], meta["kill_reason"]), (7, "cancelled"))
        self.assertEqual(self.active_rows(), [])

    def test_kill_not_running(self):
        self.cron("a", "true")
        self.assertEqual(self.rr("kill", "a", capture_output=True).returncode, 1)

    def test_interrupt_run(self):
        self.cron("a", "sleep 30")
        owner = self.rr_bg("run", "a")
        owner.stdout.readline()
        owner.send_signal(signal.SIGINT)
        self.assertEqual(owner.wait(), 128 + signal.SIGTERM)
        self.assertEqual(self.meta(self.runs("a")[0])["kill_reason"], "cancelled")

    def test_kill_orphan(self):
        self.cron("a", "sleep 30")
        pid = self.orphan("a")
        self.assertEqual(self.rr("kill", "a", capture_output=True).returncode, 0)
        self.assertFalse(process_exists(pid))
        meta = self.meta(self.runs("a")[0])
        self.assertEqual(meta["kill_reason"], "cancelled")
        self.assertNotIn("exit_code", meta)
        self.assertIn("orphaned", meta["note"])
        self.assertEqual(self.active_rows(), [])


class TestDrive(EngineTest):
    def drive(self, seconds):
        proc = self.rr_bg("drive")
        time.sleep(seconds)
        proc.send_signal(signal.SIGINT)
        out, _ = proc.communicate()
        return out.splitlines()

    def test_schedules(self):
        self.cron("fast", "true")
        (self.dir / "spec/fast/info.toml").write_text('description = "d"\nschedule = "*:*:*"\nexe = "run.sh"\n')
        lines = self.drive(3.5)
        self.assertGreaterEqual(len(self.runs("fast")), 2)
        self.assertGreaterEqual(len(lines), 2)
        self.assertRegex(lines[0], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d  fast  \d+$")

    def test_bad_specs_logged_once(self):
        self.cron("bad", "true")
        (self.dir / "spec/bad/info.toml").write_text('description = "d"\nschedule = "bogus"\nexe = "run.sh"\n')
        self.cron("ok", "true")
        self.cron("ok/nested", "true")
        self.drive(2.5)
        log = (self.root / "logs").read_text()
        self.assertEqual(log.count("bad calendar spec 'bogus'"), 1)
        self.assertEqual(log.count("ignoring nested cron ok/nested"), 1)

    def test_reclaims_orphan_on_timeout(self):
        self.cron("a", "sleep 30", "[process]\ntimeout_s = 1\n")
        pid = self.orphan("a")
        self.drive(3)
        self.assertFalse(process_exists(pid))
        meta = self.meta(self.runs("a")[0])
        self.assertEqual(meta["kill_reason"], "timeout")
        self.assertIn("orphaned", meta["note"])
        self.assertEqual(self.active_rows(), [])


if __name__ == "__main__":
    unittest.main()
