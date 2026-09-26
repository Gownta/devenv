"""Run directories and their meta.toml."""

import json
import math
import os
import time
from pathlib import Path


def human_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(ts))


_UNITS = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]


def human_duration(seconds: float) -> str:
    """At most two units, the second zero-padded, rounded up: 3m17s, 1m03s, 2h15m, 1s."""
    total = max(1, math.ceil(seconds))
    while True:
        i = next(i for i, (_, size) in enumerate(_UNITS) if total >= size)
        j = min(i + 1, len(_UNITS) - 1)
        granularity = _UNITS[j][1]
        rounded = math.ceil(total / granularity) * granularity
        if rounded == total:
            break
        total = rounded  # rounding may carry into a larger unit, e.g. 59m59s -> 1h00m
    major, major_size = _UNITS[i]
    if i == j:
        return f"{total}{major}"
    minor, minor_size = _UNITS[j]
    return f"{total // major_size}{major}{total % major_size // minor_size:02d}{minor}"


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return f"{v:.3f}"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    raise TypeError(f"can't write {type(v)} to toml")


def append_meta(rundir: Path, **fields) -> None:
    with open(rundir / "meta.toml", "a") as f:
        for k, v in fields.items():
            if v is not None:
                f.write(f"{k} = {_toml_value(v)}\n")
        f.flush()
        os.fsync(f.fileno())


def create(base: Path, ts: float) -> Path:
    """Create runs/YYYY_MM_DD__HH_MM_SS__ID under base, and point latest at it."""
    runs = base / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y_%m_%d__%H_%M_%S", time.localtime(ts))
    for i in range(10000):
        rundir = runs / f"{stamp}__{i}"
        try:
            rundir.mkdir()
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError(f"too many runs in one second in {runs}")
    tmp = base / f".latest.{os.getpid()}"
    try:
        tmp.unlink()
    except FileNotFoundError:
        pass
    tmp.symlink_to(Path("runs") / rundir.name)
    os.replace(tmp, base / "latest")
    return rundir


def finish(rundir: Path, start_ts: float, end_ts: float, exit_code=None, kill_reason=None, **extra) -> None:
    duration_s = end_ts - start_ts
    append_meta(
        rundir,
        end_time=human_time(end_ts),
        duration=human_duration(duration_s),
        duration_s=round(duration_s, 3),
        exit_code=exit_code,
        kill_reason=kill_reason,
        **extra,
    )
