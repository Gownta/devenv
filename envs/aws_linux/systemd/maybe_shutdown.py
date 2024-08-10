#!/usr/bin/python3

import subprocess
import sys
import time

from datetime import datetime, timedelta


def is_long_logout():
    last = subprocess.check_output(["last", "-n2", "--time-format", "iso"], text=True).splitlines()[1]
    if "still logged in" in last:
        return False
    iso_logout_time = last.split()[5]
    logout_time = datetime.fromisoformat(iso_logout_time)
    current_time = datetime.fromtimestamp(time.time(), tz=logout_time.tzinfo)
    delta = current_time - logout_time
    return delta > timedelta(minutes=20)


def go():
    print("maybe shutting down")
    if is_long_logout():
        print("shutting down")
        subprocess.run(["sudo", "shutdown", "+5"])


if __name__ == "__main__":
    go()
