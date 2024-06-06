import os
from dataclasses import dataclass


@dataclass
class Dst:
    short: str
    message: str = ""
    cmd: str = ""


def make_devserver_dsts(short_hostname, with_tmux=False, with_tunnel=False):
    full_hostname = short_hostname + ".facebook.com"

    ret = []
    if with_tmux:
        ret.append(Dst(
            f"{short_hostname} (tmux)",
            f"ssh'ing into {full_hostname}; automatically starting up tmux",
            f"ssh -t {full_hostname} 'tmux attach -d'",
        ))

    ret.append(Dst(
        short_hostname,
        f"ssh'ing into {full_hostname}",
        f"ssh {full_hostname}",
    ))

    if with_tunnel:
        ret.append(Dst(
            f"{short_hostname} (-L)",
            f"ssh'ing into {full_hostname}; tunneling in on port 3000",
            f"ssh {full_hostname} -L 3000:localhost:3000",
        ))

    return ret


Dsts = (
    [Dst("localhost")]
    + make_devserver_dsts("devvm2087.rva0", with_tmux=True, with_tunnel=True)
    + [Dst("localhost (tmux)", "Automatically starting up tmux", "tmux a")]
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
    if dst.message:
        print(dst.message)
    if dst.cmd:
        print(f"$ {dst.cmd}")
    return dst.cmd


if __name__ == "__main__":
    cmd = get_dst_cmd(Dsts, 1)
    if cmd:
        os.system(cmd)
