#!/usr/bin/python3


import datetime
import getpass
import os
import sys


border_left_top = "╭"
border_left_mid = "├"
border_left_bot = "╰"
border_right_top = "╮"
border_right_mid = "┤"
border_right_bot = "╯"
border_extender = "─"
N_EXTENDERS = 1


def rprompt(ncols):
    return f"\033[38;5;238m{border_extender * N_EXTENDERS + border_right_bot}\033[0m"


class Entry:
    def __init__(self, texts, fg, bg):
        assert isinstance(texts, list)
        self.texts = texts
        self.fg = fg
        self.bg = bg

    def len(self):
        return sum(len(t) for t in self.texts)


class Drawer:
    def __init__(self, starter, sep, ender, inv=False):
        self.starter = starter
        self.sep = sep
        self.inv = inv
        self.ender = ender

        self.contents = []
        self.n = 0
        self.fg = None
        self.bg = None

    def reset(self):
        self.contents.append("\033[0m")
        self.fb = None
        self.bg = None

    def set_fg(self, fg):
        if self.fg != fg:
            self.contents.extend([
                "\033[38;5;", str(fg), "m",
            ])
            self.fg = fg

    def set_bg(self, bg):
        if self.bg != bg:
            self.contents.extend([
                "\033[48;5;", str(bg), "m",
            ])
            self.bg = bg

    def add(self, entry):
        texts = entry.texts
        fg = entry.fg
        bg = entry.bg
        if not self.contents:
            self.reset()
            if self.starter:
                self.set_fg(bg)
                self.contents.append(self.starter)
                self.n += len(self.starter)
        elif self.sep:
            old_bg = self.bg
            new_fg, new_bg = old_bg, bg
            if self.inv:
                new_fg, new_bg = new_bg, new_fg
            self.set_fg(new_fg)
            self.set_bg(new_bg)
            self.contents.append(self.sep)
            self.n += len(self.sep)
        self.set_fg(fg)
        self.set_bg(bg)
        for text in texts:
            self.contents.append(text)
            self.n += len(text)

    def end(self):
        if self.contents and self.ender:
            bg = self.bg
            self.reset()
            self.set_fg(bg)
            self.contents.append(self.ender)
            self.n += len(self.ender)



def mk_fill(filler, nfill, fg):
    return ["\033[0m\033[38;5;", str(fg), "m", filler * nfill]


def get_time(now):
    fmt = " %H:%M:%S"
    return now.strftime(fmt)


def get_date(now):
    fmt = " %Y-%m-%d"
    return now.strftime(fmt)


def get_elapsed(start_ns, now):
    if not start_ns:
        return None

    start_ts = (start_ns // 1000) / 1000000
    then = datetime.datetime.fromtimestamp(start_ts)

    if then <= now:
        return None
    d = (now - then).total_seconds

    if d < 1:
        return f" {int(d * 1000)}ms"
    if d < 60:
        return f" {int(d * 10) / 10}s"
    if d < 3600:
        return f" {d // 60}m{d % 60}s"
    if d < 86400:
        return f" {d // 3600}h{(d % 3600) // 60}m"
    return f"{d // 86400}d{(d % 84600) // 3600}h{(d % 3600) // 60}m"


def get_pwd():
    d = os.getcwd()

    def prefix_find_replace(s, pre, repl):
        if s.startswith(pre):
            s = repl + s[len(pre):]
        return s

    d = prefix_find_replace(d, "/home/njormrod", "~")
    d = prefix_find_replace(d, "/Users/njormrod", "~")
    d = prefix_find_replace(d, "/data/users/njormrod", "local")

    d = prefix_find_replace(d, "~/repos", "r")
    d = prefix_find_replace(d, "local/repos", "r")

    d = prefix_find_replace(d, "r/dotfbsource/fbcode", ".f")
    if d.startswith("r/") and len(d) >= 3:
        o = ord(d[2])
        if ord("0") <= o <= ord("9"):
            n = o - ord("0")
            rest = d[3:]
            rest = prefix_find_replace("fbsource/fbcode", "f")
            rest = prefix_find_replace("configerator", "cfg")
            rest = prefix_find_replace("cfg/source", "cfg/s")
            d = f"r/{n}{rest}"

    return " " + d


def lprompt(lentries, rentries, ncols):
    ldf = lambda: Drawer("█", "", "")
    rdf = lambda: Drawer("", "", "█", inv=True)

    left_top = border_left_top + border_extender * N_EXTENDERS
    left_mid = border_left_mid + border_extender * N_EXTENDERS
    left_bot = border_left_bot + border_extender * N_EXTENDERS
    right_top = border_extender * N_EXTENDERS + border_right_top
    right_mid = border_extender * N_EXTENDERS + border_right_mid
    nc = ncols - 2 * (N_EXTENDERS + 1)

    parts = [left_top]
    ld = ldf()
    for le in lentries:
        if ld.contents





def prompt(time, ncols, env):
    now = datetime.datetime.now()

    # text color, border color
    tc = 252
    bc = 238

    # fill characters
    filler = "‧"
    nfill = ncols

    ########################################
    # Left border
    left_top = border_left_top + border_extender * N_EXTENDERS
    lbp = [
        "\033[0m\033[38;5;", str(bc), "m", left_top,
    ]
    nfill -= len(left_top)

    ########################################
    # Left components
    ld = Drawer("█", "", "")

    host_icon = env.get("HOST_ICON", None)
    if host_icon is not None:
        ld.add([" ", host_icon, "  "], tc, 236)

    pwd = get_pwd()
    ld.add(["  ", get_pwd(), "  "], tc, 21)
    ld.add(["  ", get_pwd(), "  "], tc, 21)
    ld.add(["  ", get_pwd(), "  "], tc, 21)
    ld.add(["  ", get_pwd(), "  "], tc, 21)

    ld.end()
    nfill -= ld.n

    ########################################
    # Right components
    rd = Drawer("", "", "█", inv=True)

    delta = get_elapsed(time, now)
    if delta:
        rd.add([" ", delta, " "], tc, 214)

    rd.add([" ", get_time(now), " "], tc, 28)
    rd.add([" ", get_date(now), " "], tc, 22)
    rd.add([" ", getpass.getuser(), " "], tc, 24)

    rd.end()
    nfill -= rd.n

    ########################################
    # Right border
    right_top = border_extender * N_EXTENDERS + border_right_top
    rbp = [
        "\033[0m\033[38;5;", str(bc), "m", right_top,
    ]
    nfill -= len(right_top)

    ########################################
    # Combine

    if nfill < 0:
        # we need even more lines
        left_mid = border_left_mid + border_extender * N_EXTENDERS
        right_mid = border_extender * N_EXTENDERS + border_right_mid
        parts = lbp + ld.contents 

    left_bot = border_left_bot + border_extender * N_EXTENDERS
    parts = lbp + ld.contents + ["\033[0m", "\033[38;5;", str(bc), "m", FILL * nfill] + rd.contents + rbp + ["\n", left_bot, "\033[0m"]

    if host_icon:
        parts.extend([host_icon, "\033[0m"])

    return "".join(parts)



    n_fill = ncols
    l_parts = []

    l_parts.extend([
        "\033[0m", border_color, left_top,
    ])
    n_fill -= len(left_top)



    n_fill = ncols - 2 * (N_EXTENDERS + 1) - 33
    fill = FILL * n_fill

    parts = [
        "\033[0m", border_color, left_top,
        "\033[0m", border_color, fill,
        "\033[0m", border_color, right_top,
        "\n",
        "\033[0m", border_color, left_bot,
        "\033[0m", mkLBox(252, 124, 127, sep_left, " howdy ")[1],
        "\033[0m",
        #"\033[0m", env.get("HOST_ICON", ""),
    ]
    return "".join(parts)


if __name__ == "__main__":
    assert len(sys.argv) == 3
    cols = int(sys.argv[2])
    if sys.argv[1] == "rprompt":
        print(rprompt(cols))
    else:
        print(prompt(int(sys.argv[1]), cols, os.environ))
