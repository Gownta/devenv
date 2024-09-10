#!/usr/bin/python3

import argparse
import math
import random
import shutil
import string
import sys
import time
from dataclasses import dataclass, field
from typing import Callable


Chars = {
    "binary": "01",
    "ascii": string.ascii_letters + string.digits,
}
Colors = {
    "green": [2],
    "green_hues": [22, 28, 40, 46],
}


@dataclass
class Config:
    chars: [str]
    colors: [int]
    ups: int
    ncolumns: int
    nrows: int

    drip_speed: float = 1
    drip_variance: float = 3
    drip_minl: int = 3
    drip_maxl: int = 8


    def mkRate(self):
        # return ups/speed
        ret = 1.0 * self.ups / self.drip_speed
        acceleration = math.pow(self.drip_variance, random.random())
        ret /= acceleration
        return max(1, int(ret))

    def mkMaxl(self):
        return random.randint(self.drip_minl, self.drip_maxl)

    def mkDrip(self, col):
        return Drip(
            self.mkRate(),
            self.mkMaxl(),
            random.choice(self.colors),
            self.chars,
            col,
            self.nrows,
        )

    def mkScreen(self):
        return Screen(self)


@dataclass
class Drip:
    rate: int # how many ticks between updates
    maxl: int # max rows in drip
    color: int
    chars: [str]
    col: int
    end_row: int

    soon: int = 99999
    ccs: list = field(default_factory=list)
    row: int = 0
    done: bool = False

    def __post_init__(self):
        self.ccs = [random.choice(self.chars) for i in range(self.maxl)]

    def erase(self):
        for i in range(len(self.ccs)):
            r = self.row - i
            if 0 < r <= self.end_row:
                print(f"\033[{r};{self.col}H ", end="")

    def draw(self):
        for i, c in enumerate(self.ccs):
            r = self.row - i
            if 0 < r <= self.end_row:
                print(f"\033[{r};{self.col}H\033[38;5;{self.color}m{c}\033[0m", end="")

    def update(self, config):
        self.soon += 1
        if self.soon >= self.rate:
            self.soon = 0
            self.erase()
            self.row += 1
            self.draw()
            if self.row - self.maxl > self.end_row:
                self.done = True
        else:
            pass


@dataclass
class Screen:
    config: Config
    dripss: list = field(default_factory=list)

    def __post_init__(self):
        self.dripss = [[] for c in range(self.config.ncolumns)]

    def p_spawn(self, ndrips, cdrips):
        # don't spawn too close to a previous spawn
        if cdrips and cdrips[-1].row < 3:
            return None

        return 1.0 / self.config.ups / 5
        return 1.0 / self.config.ups / 25

        target_ncdrips = 3 + math.sqrt(self.config.nrows / 10)
        target_ndrips = self.config.ncolumns * target_ncdrips
        total_off = target_ndrips - ndrips
        column_off = max(target_ncdrips - len(cdrips), 0)

        CW = 5
        A = 0.3
        t = max(A * (CW * column_off + total_off), 1)

        return min(1.0 / self.config.ups / t, 1)

    def update(self):
        ndrips = sum(len(ds) for ds in self.dripss)
        for col, drips in enumerate(self.dripss):
            p_spawn = self.p_spawn(ndrips, drips)
            if p_spawn is not None and random.random() < p_spawn:
                drip = self.config.mkDrip(col + 1)
                drips.append(drip)
            for i, drip in enumerate(drips):
                drip.update(self.config)
                if i > 0:
                    next_drip = drips[i - 1]
                    ndccs = len(next_drip.ccs)
                    if ndccs:
                        top = next_drip.row - ndccs + 1
                        if drip.row >= top:
                            next_drip.ccs.pop()
                            if not next_drip.ccs:
                                next_drip.done = True
            j = 0
            while j < len(drips):
                if drips[j].done:
                    drips.pop(j)
                else:
                    j += 1


def get_args(argv):
    parser = argparse.ArgumentParser(
        "matrix",
        description="Matrix drip screen",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--ups",
        default=60,
        type=int,
        help="Updates per second",
    )
    parser.add_argument(
        "--charset",
        choices=list(Chars.keys()) + ["random"],
        default="ascii",
        help="What characterset to use in the waterfall",
    )
    parser.add_argument(
        "--colors",
        choices=list(Colors.keys()) + ["random"],
        default="green_hues",
        help="What colorset to use in the waterfall",
    )

    parser.add_argument(
        "-s",
        "--speed",
        type=float,
        default=1.0,
        help="Average speed of drips",
    )

    return parser.parse_args(argv)


def config_from_args(args):
    charkey = args.charset
    if charkey == "random":
        charkey = random.choice(list(Chars.keys()))
    colorkey = args.colors
    if colorkey == "random":
        colorkey = random.choice(list(Colors.keys()))
    ncolumns, nrows = shutil.get_terminal_size()
    return Config(
        Chars[charkey],
        Colors[colorkey],
        args.ups,
        ncolumns,
        nrows,
        drip_speed=args.speed,
    )


def main(argv):
    args = get_args(argv)
    config = config_from_args(args)
    screen = config.mkScreen()
    try:
        # clear screen
        print("\033[2J", end="", flush=True)
        while True:
            screen.update()
            # reset the cursor, flush, and sleep
            print("\033[H\033[0m", end="", flush=True)
            time.sleep(1.0 / config.ups)
    except KeyboardInterrupt:
        pass
    finally:
        # clear screen, reset cursor, reset color
        print("\033[2J\033[H\033[0m", end="", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
