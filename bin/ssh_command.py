import os
import select
import sys
import termios
import time
from dataclasses import dataclass


@dataclass
class Dst:
    short: str
    message: str = ""
    cmd: str = ""
    get_yubi: bool = False


# A YubiKey OTP arrives as a fixed-length burst of 32 characters
YUBIKEY_LENGTH = 32


def get_yubikey(length=YUBIKEY_LENGTH):
    """
    Capture a YubiKey OTP from the terminal.

    A YubiKey "types" its one-time password as a rapid burst of characters.
    We read raw, un-echoed input until at least `length` characters have
    arrived and at least 1/length seconds have elapsed, then return the last
    `length` characters -- dropping any stray leading input (such as the
    newline left over from the menu selection).

    As the burst streams in we echo a masked progress indicator: the first
    four characters verbatim (so you can see your key fired) and every
    character after that as a '*'.
    """
    print("Activate YubiKey to ssh in: ", end="", flush=True)
    min_elapsed = 1.0 / length

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] &= ~(termios.ICANON | termios.ECHO)  # lflags: no canonical, no echo
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, new)

    buf = []
    last = None
    try:
        while True:
            # Finalize once we have enough characters and input has gone idle
            # for the settle window -- the burst is over. Reading past `length`
            # this way lets the trailing last-`length` slice drop stray leading
            # input (e.g. the newline left from the menu selection).
            if len(buf) >= length and last is not None:
                idle = time.monotonic() - last
                if idle >= min_elapsed:
                    break
                timeout = min_elapsed - idle
            else:
                timeout = None  # wait (indefinitely) for more of the burst
            ready, _, _ = select.select([fd], [], [], timeout)
            if ready:
                raw = os.read(fd, 1)
                if not raw:  # EOF
                    break
                ch = raw.decode("ascii", "replace")
                buf.append(ch)
                # Echo masked progress: the first four characters verbatim,
                # the rest as '*'. Non-printable stray input is masked too,
                # so a leading newline can't corrupt the line.
                shown = ch if (len(buf) <= 4 and ch.isprintable()) else "*"
                sys.stdout.write(shown)
                sys.stdout.flush()
                last = time.monotonic()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        # Terminate the masked echo line before returning.
        sys.stdout.write("\n")
        sys.stdout.flush()

    return "".join(buf[-length:])


def make_devserver_dsts(short_hostname, with_eternal=False, with_tunnel=False, envstr=""):
    full_hostname = short_hostname + ".facebook.com"

    ret = []
    if with_eternal:
        ret.append(Dst(
            f"{short_hostname} (eternal)",
            f"eternally connecting to {full_hostname}",
            f"{envstr}dev connect -e -n {full_hostname}",
            get_yubi=True,
        ))

    ret.append(Dst(
        f"{short_hostname} (ssh)",
        f"ssh'ing into {full_hostname}",
        f"{envstr}ssh {full_hostname}",
        get_yubi=True,
    ))

    if with_tunnel:
        ret.append(Dst(
            f"{short_hostname} (-L)",
            f"ssh'ing into {full_hostname}; tunneling in on port 3000",
            f"ssh {full_hostname} -L 3000:localhost:3000",
            get_yubi=True,
        ))

    return ret


Dsts = (
    [
        Dst("localhost (tmux)", "Automatically starting up tmux", "tmux_go"),
        Dst(
            "OnDemand (eternal tmux)",
            "Connecting to WWW+FBSource+Configerator OnDemand",
            "TERM=tmux-256color dev connect --type www_fbsource_configerator --connection eternalterminal --release-without-prompt",
            get_yubi=True,
        ),
    ]
    + make_devserver_dsts("devvm7569.cco0", with_eternal=True, envstr="TERM=tmux-256color ")
    + make_devserver_dsts("devvm50895.cco0", with_eternal=True, envstr="TERM=tmux-256color ")
    + [Dst("localhost")]
)
#host[3]="alpha-pi"
#full[3]="192.168.0.21"


def get_dst_cmd(dsts, default=None):
    print("Commander, where can I ssh you?")
    for i, dst in enumerate(dsts):
        dflts = ""
        if default == i:
            dflts = "\t\t(default)"
        print(f"  ({i}) {dst.short}{dflts}")
    print("")

    def in_dst(n):
        flavor = "Destination"
        while True:
            dst = input(f"{flavor} [0-{n-1}]: ")
            if dst == "" and default is not None:
                return default
            try:
                i = int(dst)
                if i < 0 or i >= n:
                    flavor = "We haven't conquered that host yet."
                else:
                    return i
            except Exception:
                flavor = "That destination is above your pay grade, sir."

    dst_idx = in_dst(len(dsts))
    dst = dsts[dst_idx]
    cmd = dst.cmd
    if dst.message:
        print(dst.message)
    if cmd:
        print(f"$ {cmd}")
    if dst.get_yubi:
        cmd += " --yubi " + get_yubikey()
    return cmd


if __name__ == "__main__":
    cmd = get_dst_cmd(Dsts, 2)
    if cmd:
        os.system(cmd)
