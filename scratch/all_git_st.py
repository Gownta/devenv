#!/usr/bin/python3
"""
Print github logo
Green if all repos in dev/ have no local changes
Red otherwise
"""

import os
import subprocess
from pathlib import Path

desired = """
On branch {0}
Your branch is up to date with 'origin/{0}'.

nothing to commit, working tree clean
""".strip()

def all_clear():
    for repo in Path("~/dev").expanduser().iterdir():
        dg = repo / ".git"
        if not dg.exists():
            # not a git repo
            continue
        head = dg / "HEAD"
        target = head.read_text().split("/")[-1].strip()
        #print(f"{repo} {target}")
        desired_target = desired.format(target)
        os.chdir(repo.resolve())
        r = subprocess.run(["git", "status"], capture_output=True, text=True)
        if r.returncode != 0 or r.stderr:
            return None
        if r.stdout.strip() != desired_target:
            return False
    return True


def to_color(r):
    if r is True:
        # green
        return 40
    if r is False:
        # orange
        return 208
    # red
    return 196


def colorize(c):
    #return f"\033[38;5;196m\033[0m"
    #return f"#[fg=]\033[38;5;196m\033[0m"


r = all_clear()
c = to_color(r)
#print(colorize(c))
if r is True:
    print("t")
elif r is False:
    print("f")
else:
    print("n")
