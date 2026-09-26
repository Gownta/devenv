"""Loading config.toml and the cron specs under spec/."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

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
    # Searched in order, like $PATH: the first dir defining a cron name wins.
    spec_dirs: List[Path]
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
    # Changes whenever info.toml changes or the cron moves, so drive can reschedule.
    fingerprint: str

    @property
    def is_ai(self) -> bool:
        return self.provider is not None


def load_config(path: Optional[Path] = None, specdirs: Sequence[str] = (), local_specdir: bool = True) -> Config:
    """specdirs are appended after the local spec_dir (unless local_specdir is False) and $CHRONARCH_SPECDIRS."""
    path = Path(path or DEFAULT_CONFIG).resolve()
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    root = os.environ.get("CHRONARCH_ROOT") or raw.get("root")
    if not root:
        raise SpecError(f"$CHRONARCH_ROOT is unset and {path} has no `root`")
    dirs = [str(path.parent / os.path.expanduser(raw.get("spec_dir", "spec")))] if local_specdir else []
    dirs += [d for d in os.environ.get("CHRONARCH_SPECDIRS", "").split(":") if d]
    dirs += specdirs
    spec_dirs = []
    for d in dirs:
        resolved = Path(os.path.expanduser(d)).resolve()
        if resolved not in spec_dirs:
            spec_dirs.append(resolved)
    return Config(
        path=path,
        root=Path(os.path.expanduser(root)).resolve(),
        spec_dirs=spec_dirs,
        sweep_interval_s=float(raw.get("sweep_interval_s", 60)),
        raw=raw,
    )


def discover(cfg: Config) -> Tuple[List[str], List[str]]:
    """Names of all crons in the spec dirs, and errors for crons that are ignored (nested or shadowed)."""
    found: Dict[str, Path] = {}
    errors = []
    for spec_dir in cfg.spec_dirs:
        for dirpath, dirnames, filenames in os.walk(spec_dir):
            dirnames.sort()
            if "info.toml" not in filenames:
                continue
            name = os.path.relpath(dirpath, spec_dir)
            if name in found:
                errors.append(f"ignoring cron {name} in {spec_dir}: shadowed by {found[name]}")
            else:
                found[name] = spec_dir
            for sub, _, files in os.walk(dirpath):
                if sub != dirpath and "info.toml" in files:
                    errors.append(f"ignoring nested cron {os.path.relpath(sub, spec_dir)} inside {name} in {spec_dir}")
            dirnames[:] = []
    return sorted(found), errors


def find_cron(cfg: Config, name: str) -> Path:
    """The spec root of the named cron, from the first spec dir that has it."""
    for spec_dir in cfg.spec_dirs:
        spec_root = (spec_dir / name).resolve()
        if spec_dir in spec_root.parents and (spec_root / "info.toml").is_file():
            return spec_root
    raise SpecError(f"{name}: no such cron in {':'.join(map(str, cfg.spec_dirs)) or '(no spec dirs)'}")


def load_cron(cfg: Config, name: str) -> Cron:
    spec_root = find_cron(cfg, name)
    data = (spec_root / "info.toml").read_bytes()
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
        fingerprint=hashlib.sha256(str(spec_root).encode() + b"\0" + data).hexdigest(),
    )
