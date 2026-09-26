import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import config as configs
import rundir
from config import SpecError
from schedule import next_elapse, next_fire


class TestHumanDuration(unittest.TestCase):
    def test_examples(self):
        cases = {
            0: "1s",
            0.2: "1s",
            9.001: "10s",
            59.5: "1m00s",
            63: "1m03s",
            197: "3m17s",
            3599.2: "1h00m",
            3661: "1h02m",
            8074: "2h15m",
            86399: "1d00h",
            90000: "1d01h",
            200000: "2d08h",
        }
        for seconds, expected in cases.items():
            with self.subTest(seconds=seconds):
                self.assertEqual(rundir.human_duration(seconds), expected)


class TestSchedule(unittest.TestCase):
    def test_local_time(self):
        now = time.time()
        t = time.localtime(next_elapse("daily", now))
        self.assertEqual((t.tm_hour, t.tm_min, t.tm_sec), (0, 0, 0))
        self.assertLessEqual(next_elapse("daily", now) - now, 86400 + 3600)

    def test_strictly_after(self):
        base = 1790000100  # a multiple of 5 seconds
        self.assertEqual(next_elapse("*:*:0/5", base), base + 5)

    def test_never(self):
        self.assertIsNone(next_elapse("2020-01-01", time.time()))

    def test_bad(self):
        with self.assertRaises(SpecError):
            next_elapse("bogus", time.time())

    def test_next_fire_takes_earliest(self):
        base = 1790000100
        self.assertEqual(next_fire(["*:*:0/10", "*:*:3/10"], base), base + 3)


class TestSpecs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "config.toml").write_text(
            'spec_dir = "spec"\n'
            '[ai]\nprovider = "claude"\n[ai.claude]\nmodel = "opus"\neffort = "high"\nargs = ["--x"]\n'
            '[process]\ntimeout_s = 100\n'
        )
        self.saved_env = {k: os.environ.pop(k) for k in ("CHRONARCH_ROOT", "CHRONARCH_SPECDIRS") if k in os.environ}
        os.environ["CHRONARCH_ROOT"] = str(self.dir / "root")
        self.cfg = configs.load_config(self.dir / "config.toml")

    def tearDown(self):
        os.environ.pop("CHRONARCH_ROOT", None)
        os.environ.update(self.saved_env)
        self.tmp.cleanup()

    def spec(self, name, info, spec_dir="spec"):
        d = self.dir / spec_dir / name
        d.mkdir(parents=True)
        (d / "info.toml").write_text(info)

    def test_discover(self):
        self.spec("a", "")
        self.spec("b/c", "")
        self.spec("b/c/d", "")
        names, errors = configs.discover(self.cfg)
        self.assertEqual(names, ["a", "b/c"])
        self.assertEqual(errors, [f"ignoring nested cron b/c/d inside b/c in {self.dir / 'spec'}"])

    def test_defaults(self):
        self.spec("a", 'description = "d"\nschedule = "daily"\nexe = "x.sh"\n')
        cron = configs.load_cron(self.cfg, "a")
        self.assertEqual(cron.schedules, ["daily"])
        self.assertEqual(cron.exe, self.cfg.spec_dirs[0] / "a" / "x.sh")
        self.assertEqual(cron.root_dir, self.cfg.spec_dirs[0] / "a")
        self.assertEqual(cron.timeout_s, 100)
        self.assertEqual(cron.max_concurrent, 1)
        self.assertFalse(cron.is_ai)

    def test_ai_overrides(self):
        self.spec(
            "a",
            'description = "d"\nschedule = ["daily", "weekly"]\nexe = "p.md"\n'
            '[ai]\nmodel = "haiku"\n[process]\nroot_dir = "/tmp"\ntimeout_s = 5\nmax_concurrent = 3\n',
        )
        cron = configs.load_cron(self.cfg, "a")
        self.assertEqual((cron.provider, cron.model, cron.effort, cron.ai_args), ("claude", "haiku", "high", ["--x"]))
        self.assertEqual((cron.root_dir, cron.timeout_s, cron.max_concurrent), (Path("/tmp"), 5, 3))

    def test_errors(self):
        self.spec("missing", 'description = "d"\nexe = "x"\n')
        self.spec("provider", 'description = "d"\nschedule = "daily"\nexe = "p.md"\n[ai]\nprovider = "x"\n')
        for name in ["missing", "provider", "nonexistent", "../escape"]:
            with self.subTest(name=name), self.assertRaises(SpecError):
                configs.load_cron(self.cfg, name)

    def test_specdir_order(self):
        os.environ["CHRONARCH_SPECDIRS"] = f"{self.dir / 'e1'}::{self.dir / 'e2'}:{self.dir / 'spec'}"
        try:
            cfg = configs.load_config(self.dir / "config.toml", [str(self.dir / "c1"), str(self.dir / "e1")])
            self.assertEqual(cfg.spec_dirs, [self.dir / d for d in ["spec", "e1", "e2", "c1"]])
            cfg = configs.load_config(self.dir / "config.toml", [str(self.dir / "c1")], local_specdir=False)
            self.assertEqual(cfg.spec_dirs, [self.dir / d for d in ["e1", "e2", "spec", "c1"]])
        finally:
            del os.environ["CHRONARCH_SPECDIRS"]

    def test_shadowing(self):
        info = 'description = "d"\nschedule = "daily"\nexe = "x.sh"\n'
        self.spec("a", info)
        self.spec("a", info, "other")
        self.spec("b", info, "other")
        cfg = configs.load_config(self.dir / "config.toml", [str(self.dir / "other")])
        names, errors = configs.discover(cfg)
        self.assertEqual(names, ["a", "b"])
        self.assertEqual(errors, [f"ignoring cron a in {self.dir / 'other'}: shadowed by {self.dir / 'spec'}"])
        self.assertEqual(configs.load_cron(cfg, "a").spec_root, self.dir / "spec" / "a")
        self.assertEqual(configs.load_cron(cfg, "b").spec_root, self.dir / "other" / "b")
        unshadowed = configs.load_config(self.dir / "config.toml", [str(self.dir / "other")], local_specdir=False)
        self.assertEqual(configs.load_cron(unshadowed, "a").spec_root, self.dir / "other" / "a")
        # Same info.toml, different dir: drive must notice the move.
        self.assertNotEqual(configs.load_cron(cfg, "a").fingerprint, configs.load_cron(unshadowed, "a").fingerprint)

    def test_root(self):
        self.assertEqual(self.cfg.root, self.dir / "root")
        del os.environ["CHRONARCH_ROOT"]
        with self.assertRaisesRegex(SpecError, "no chronarch root"):
            configs.load_config(self.dir / "config.toml")
        config = self.dir / "config.toml"
        config.write_text('root = "from_config"\n' + config.read_text())
        self.assertEqual(configs.load_config(config).root, self.dir / "from_config")
        os.environ["CHRONARCH_ROOT"] = str(self.dir / "env")
        self.assertEqual(configs.load_config(self.dir / "config.toml").root, self.dir / "env")


class TestRundir(unittest.TestCase):
    def test_create_same_second(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ts = time.time()
            a, b = rundir.create(base, ts), rundir.create(base, ts)
            self.assertTrue(a.name.endswith("__0"))
            self.assertTrue(b.name.endswith("__1"))
            self.assertEqual((base / "latest").resolve(), b.resolve())
            self.assertEqual(os.readlink(base / "latest"), f"runs/{b.name}")


if __name__ == "__main__":
    unittest.main()
