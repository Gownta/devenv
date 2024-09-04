#!/usr/bin/python3


import datetime
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
    return ""
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


def get_time(now):
    fmt = " %H:%M:%S"
    return now.strftime(fmt)


def get_date(now):
    fmt = " %Y-%m-%d"
    return now.strftime(fmt)


def get_elapsed(start_ts, now, has_us):
    if not start_ts:
        return None
    then = datetime.datetime.fromtimestamp(start_ts)

    if then > now:
        return "time error"
    d = (now - then).total_seconds()

    if not has_us and d < 2:
        return None

    if d < 1:
        return f" {int(d * 1000)}ms"
    if d < 60:
        if has_us:
            return f" {int(d * 10) / 10}s"
        return f" {int(d)}s"
    if d < 3600:
        return f" {int(d / 60)}m{int(d % 60)}s"
    if d < 86400:
        return f" {int(d / 3600)}h{int((d % 3600) / 60)}m"
    return f" {int(d / 86400)}d {int((d % 84600) / 3600)}h{int((d % 3600) / 60)}m"


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
    d = prefix_find_replace(d, "r/configerator", "r/cfg")
    d = prefix_find_replace(d, "r/cfg/source", "r/cfg/s")
    if d.startswith("r/") and len(d) >= 3:
        o = ord(d[2])
        if ord("0") <= o <= ord("9"):
            n = o - ord("0")
            rest = d[3:]
            rest = prefix_find_replace(rest, "fbsource/fbcode", "f")
            rest = prefix_find_replace(rest, "configerator", "cfg")
            rest = prefix_find_replace(rest, "cfg/source", "cfg/s")
            d = f"r/{n}{rest}"

    return " " + d


def lprompt(lentries, rentries, trentries, ncols):
    ############################################################
    ### Function-globals
    ############################################################

    # The ultimate return, in parts
    parts = []

    # Drawer factories
    ldf = lambda: Drawer("█", "", "")
    rdf = lambda: Drawer("", "", "█", inv=True)


    ############################################################
    ### Borders
    ############################################################

    bc = 238  # border_color
    filler = "‧"

    def mk_border(content):
        return ["\033[0m\033[38;5;", str(bc), "m", content]

    left_top = mk_border(border_left_top + border_extender * N_EXTENDERS)
    left_mid = mk_border(border_left_mid + border_extender * N_EXTENDERS)
    left_bot = mk_border(border_left_bot + border_extender * N_EXTENDERS)
    right_top = mk_border(border_extender * N_EXTENDERS + border_right_top)
    right_mid = mk_border(border_extender * N_EXTENDERS + border_right_mid)
    right_bot = mk_border(border_extender * N_EXTENDERS + border_right_bot)

    # Number of free columns, excluding borders
    nc = ncols - 2 * (N_EXTENDERS + 1)

    def mk_fill(nfill):
        return ["\033[0m\033[38;5;", str(bc), "m", filler * nfill]


    ############################################################
    ### Multi-line handling
    ############################################################

    used_left_top = False
    used_right_top = False

    ld = None

    def open_ld():
        nonlocal ld
        nonlocal used_left_top
        left = left_mid if used_left_top else left_top
        used_left_top = True

        parts.extend(left)
        ld = ldf()

    def close_ld():
        nonlocal ld
        nonlocal used_right_top
        right = right_mid if used_right_top else right_top
        used_right_top = True

        ld.end()
        parts.extend(ld.contents)
        parts.extend(mk_fill(nc - ld.n))
        parts.extend(right)
        parts.append("\n")

    if trentries:
        trd = rdf()
        for tre in trentries:
            trd.add(tre)
        lead = ncols - trd.n - N_EXTENDERS - 1
        parts.append(" " * lead)
        parts.extend(trd.contents)
        parts.extend(right_top)
        used_right_top = True
        parts.append("\n")

    open_ld()
    for le in lentries:
        # Normal case: the next entry fits
        # -1 for the ender
        if ld.n + le.len() <= nc - 1:
            ld.add(le)
            continue

        # ok, it doesn't fit
        # maybe close the existing ld
        if ld.contents:
            close_ld()
            open_ld()

        # does this entry fit?
        if le.len() <= nc - 1:
            ld.add(le)
            continue

        # ok, this entry alone is too big
        ld.add(le)
        parts.extend(ld.contents)
        parts.append("\n")
        used_right_top = True
        open_ld()

    # Make the rd, which doesn't include dynamic sizes, so fits
    rd = rdf()
    for re in rentries:
        rd.add(re)
    rd.end()

    # Combine the ld and rd, if possible
    if not ld.contents:
        parts.extend(mk_fill(nc - rd.n))
        parts.extend(rd.contents)

        right = right_mid if used_right_top else right_top
        used_right_top = True
        parts.extend(right)
    elif ld.n + rd.n <= nc - 1:
        ld.end()
        parts.extend(ld.contents)
        parts.extend(mk_fill(nc - ld.n - rd.n))
        parts.extend(rd.contents)

        right = right_mid if used_right_top else right_top
        used_right_top = True
        parts.extend(right)
    else:
        close_ld()
        open_ld()
        parts.extend(mk_fill(nc - rd.n))
        parts.extend(rd.contents)
        parts.extend(right_mid)


    ############################################################
    ### Finishing touches
    ############################################################

    # No trailing newline.
    # Have regular PROMPT and RPROMPT vars for the line-of

    return "".join(parts)


def prompt(time, ncols, env, ec, whole_cmd, has_us):
    # text color
    tc = 252
    now = datetime.datetime.now()

    lentries = [
        Entry([" ", env.get("HOST_ICON", ""), "  "], tc, 236),
        Entry([" ", get_pwd(), " "], tc, 21),
    ]
    rentries = [
        Entry([" ", get_time(now), " "], tc, 28),
        Entry([" ", get_date(now), " "], tc, 22),
        #Entry([" ", getpass.getuser(), " "], tc, 24),
    ]

    trentries = []
    if ec:
        trentries.append(Entry([" Exit ", str(ec), " "], tc, 1))
    delta = get_elapsed(time, now, has_us)
    if delta:
        trentries.append(Entry([" ", delta, " "], tc, 166))
    if whole_cmd:
        cmd = whole_cmd.split()[0].rstrip("/").split("/")[-1]
        if cmd:
            trentries.append(Entry([" ", cmd, " "], tc, 89))

    return lprompt(lentries, rentries, trentries, ncols)


if __name__ == "__main__":
    try:
        assert len(sys.argv) == 5
        cols = int(sys.argv[2]) - 1 # -1 because RPROMPT doesn't go to the end

        t = sys.argv[1]
        if t == "0":
            start = 0
            has_us = False
        else:
            if t.endswith("N"):
                # mac only has second-granularity
                start = int(t[:-1])
                has_us = False
            else:
                s = int(t[:-9])
                us = int(t[-9:-3])
                start = s + us / 1000000
                has_us = True

        exit_code = int(sys.argv[3])
        whole_cmd = sys.argv[4]
        print(prompt(start, cols, os.environ, exit_code, whole_cmd, has_us))
    except:
        print("prompt_gen failed")
        print(" ".join(sys.argv))
