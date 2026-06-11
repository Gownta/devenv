#!/usr/bin/python3

"""
Append a smartlog monkeypatch to each repo's .hg/hgrc.

At login time on an OnDemand a repo may not be cloned/mounted yet, so we
keep retrying any repo whose hgrc we couldn't open, sleeping briefly
between attempts and giving up entirely after a timeout.
"""

import os
import time


# Repos to patch. Paths are run through expanduser.
REPO_PATHS = [
    "~/fbsource",
]

# Text appended to an unpatched hgrc. COMPLETE_MARKER must be its last line.
COMPLETE_MARKER = "# njo monkeypatch complete"
MONKEYPATCH = f"""\
# njo monkeypatch begin
[smartlog]
names = master
{COMPLETE_MARKER}
"""

TIMEOUT_SECONDS = 30
RETRY_INTERVAL_SECONDS = 0.1


def hgrc_path(repo_path):
    return os.path.join(os.path.expanduser(repo_path), ".hg", "hgrc")


def already_patched(path):
    with open(path) as f:
        lines = f.read().strip().splitlines()
    return bool(lines) and lines[-1] == COMPLETE_MARKER


def append_monkeypatch(path):
    with open(path) as f:
        content = f.read()
    # Make sure the monkeypatch begins on a fresh line.
    prefix = "" if content == "" or content.endswith("\n") else "\n"
    with open(path, "a") as f:
        f.write(prefix + MONKEYPATCH)


def fix(repo_path):
    """Patch one repo. Return True if fixed (or already was), False if the
    hgrc couldn't be opened and the repo should be retried."""
    path = hgrc_path(repo_path)
    try:
        if not already_patched(path):
            append_monkeypatch(path)
        return True
    except OSError:
        return False


def go():
    unfixed = list(REPO_PATHS)
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while unfixed:
        unfixed = [repo for repo in unfixed if not fix(repo)]
        if not unfixed or time.monotonic() >= deadline:
            break
        time.sleep(RETRY_INTERVAL_SECONDS)


if __name__ == "__main__":
    go()
