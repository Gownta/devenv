"""Loading config.toml and the cron specs under spec/."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import tomllib
except ImportError:  # python < 3.11
    import tomli as tomllib


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config.toml"
AI_PROVIDERS = ("claude", "codex")


class SpecError(Exception):
    pass


@dataclass
class Config:
    path: Path
    root: Path
    spec_dir: Path
    sweep_interval_s: float
    raw: dict

    @property
    def db_path(self) -> Path:
        return self.root / "db"

    @property
    def log_path(self) -> Path:
        return self.root / "logs"

    def rundir_base(self, name: str) -> Path:
        return self.root / "rundirs" / name


@dataclass
class Cron:
    name: str
    spec_root: Path
    description: str
    schedules: List[str]
    exe: Path
    # Set iff exe is a .md file.
    provider: Optional[str]
    model: Optional[str]
    effort: Optional[str]
    ai_args: List[str]
    timeout_s: float
    root_dir: Path
    max_concurrent: int
    kill_grace_s: float
    # Changes whenever info.toml changes, so drive can reschedule.
    fingerprint: str

    @property
    def is_ai(self) -> bool:
        return self.provider is not None


def load_config(path: Optional[Path] = None) -> Config:
    path = Path(path or DEFAULT_CONFIG).resolve()
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    root = os.environ.get("CHRONARCH_ROOT") or raw.get("root")
    if not root:
        raise SpecError(f"$CHRONARCH_ROOT is unset and {path} has no `root`")
    spec_dir = path.parent / os.path.expanduser(raw.get("spec_dir", "spec"))
    return Config(
        path=path,
        root=Path(os.path.expanduser(root)).resolve(),
        spec_dir=spec_dir.resolve(),
        sweep_interval_s=float(raw.get("sweep_interval_s", 60)),
        raw=raw,
    )


def discover(cfg: Config) -> Tuple[List[str], List[str]]:
    """Names of all crons under spec_dir, and errors for nested crons (which are ignored)."""
    names, errors = [], []
    for dirpath, dirnames, filenames in os.walk(cfg.spec_dir):
        dirnames.sort()
        if "info.toml" not in filenames:
            continue
        name = os.path.relpath(dirpath, cfg.spec_dir)
        names.append(name)
        for sub, _, files in os.walk(dirpath):
            if sub != dirpath and "info.toml" in files:
                errors.append(f"ignoring nested cron {os.path.relpath(sub, cfg.spec_dir)} inside {name}")
        dirnames[:] = []
    return names, errors


def load_cron(cfg: Config, name: str) -> Cron:
    spec_root = (cfg.spec_dir / name).resolve()
    if cfg.spec_dir not in spec_root.parents:
        raise SpecError(f"{name}: not inside {cfg.spec_dir}")
    info_path = spec_root / "info.toml"
    try:
        data = info_path.read_bytes()
    except FileNotFoundError:
        raise SpecError(f"{name}: no such cron ({info_path} does not exist)")
    try:
        info = tomllib.loads(data.decode())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise SpecError(f"{name}: bad info.toml: {e}")

    def need(key, types):
        if key not in info:
            raise SpecError(f"{name}: info.toml is missing `{key}`")
        if not isinstance(info[key], types):
            raise SpecError(f"{name}: `{key}` has the wrong type")
        return info[key]

    description = need("description", str)
    schedules = need("schedule", (str, list))
    if isinstance(schedules, str):
        schedules = [schedules]
    if not schedules or not all(isinstance(s, str) for s in schedules):
        raise SpecError(f"{name}: `schedule` must be a string or a list of strings")
    exe = spec_root / os.path.expanduser(need("exe", str))

    process_defaults = cfg.raw.get("process", {})
    process = {**process_defaults, **info.get("process", {})}
    root_dir = spec_root / os.path.expanduser(process.get("root_dir", "."))

    provider = model = effort = None
    ai_args: List[str] = []
    if exe.suffix == ".md":
        ai_defaults = cfg.raw.get("ai", {})
        ai = info.get("ai", {})
        provider = ai.get("provider", ai_defaults.get("provider", "claude"))
        if provider not in AI_PROVIDERS:
            raise SpecError(f"{name}: unknown ai provider {provider!r}")
        provider_defaults = ai_defaults.get(provider, {})
        model = ai.get("model", provider_defaults.get("model"))
        effort = ai.get("effort", provider_defaults.get("effort"))
        ai_args = list(provider_defaults.get("args", []))

    return Cron(
        name=name,
        spec_root=spec_root,
        description=description,
        schedules=schedules,
        exe=exe,
        provider=provider,
        model=model,
        effort=effort,
        ai_args=ai_args,
        timeout_s=float(process.get("timeout_s", 3600)),
        root_dir=root_dir.resolve(),
        max_concurrent=int(process.get("max_concurrent", 1)),
        kill_grace_s=float(process.get("kill_grace_s", 10)),
        fingerprint=hashlib.sha256(data).hexdigest(),
    )
