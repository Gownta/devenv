#!/usr/bin/python3


import math
import subprocess
import sys
import time

from datetime import datetime, timedelta


def logout_length(user):
    last = subprocess.check_output(["last", "-n2", "--time-format", "iso", user], text=True).splitlines()[0]
    print(last)
    if "still logged in" in last:
        return timedelta()
    iso_logout_time = last.split()[5]
    logout_time = datetime.fromisoformat(iso_logout_time)
    current_time = datetime.fromtimestamp(time.time(), tz=logout_time.tzinfo)
    delta = current_time - logout_time
    return delta


def go():
    user = "njormrod"
    delta = logout_length(user)
    minutes = math.floor(delta.total_seconds()) // 60
    print(f"User {user} has been logged out for {minutes} minutes")
    if minutes >= 20:
        print("Shutting down")
        subprocess.run(["sudo", "shutdown", "+5", "njormrod not logged in; shutting down; `sudo shutdown -c` to cancel"])
    else:
        print("Doing nothing")


if __name__ == "__main__":
    go()
