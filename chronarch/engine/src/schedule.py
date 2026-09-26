"""systemd calendar specs, evaluated by systemd-analyze itself."""

import subprocess
from datetime import datetime, timezone
from typing import Iterable, Optional

from config import SpecError


def next_elapse(spec: str, after: float) -> Optional[float]:
    """First time strictly after `after` (epoch seconds) matching `spec`, or None if never."""
    proc = subprocess.run(
        ["systemd-analyze", "calendar", "--iterations=1", f"--base-time=@{int(after)}", spec],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SpecError(f"bad calendar spec {spec!r}: {proc.stderr.strip()}")
    # Specs are evaluated in local time. "Next elapse" is local; "(in UTC)" is only shown if local isn't UTC.
    fields = {}
    for line in proc.stdout.splitlines():
        key, _, value = line.partition(":")
        fields.setdefault(key.strip(), value.strip())
    value = fields.get("(in UTC)", fields.get("Next elapse"))
    if value == "never":
        return None
    if not value or not value.endswith(" UTC"):
        raise SpecError(f"can't parse systemd-analyze output for {spec!r}: {proc.stdout!r}")
    ts = datetime.strptime(value, "%a %Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc).timestamp()
    # --base-time has whole-second resolution.
    return ts if ts > after else next_elapse(spec, after + 1)


def next_fire(specs: Iterable[str], after: float) -> Optional[float]:
    times = [t for t in (next_elapse(s, after) for s in specs) if t is not None]
    return min(times, default=None)
