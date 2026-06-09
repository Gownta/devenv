# Italics (and truecolor) over ssh + tmux

I want iterm and tmux to render italic text (and 24-bit truecolor).

## How TERM works

The TERM variable names which terminal you're using. Apps don't read it directly;
they look it up in the **terminfo database** (via ncurses) to learn which escape
codes the terminal understands -- e.g. `sitm`/`ritm` enable/disable italics.

When you ssh, your local TERM is passed through to the server, and the server only
emits markup that this terminal type is recorded as supporting. With tmux there are
two TERMs in play:
- the **outer** TERM = the real terminal tmux talks to (iTerm). tmux uses the
  outer terminfo to decide what it can forward upstream.
- the **inner** TERM = what tmux presents to programs inside it, set by
  `default-terminal` in tmux.conf (I use `tmux-256color`).

For italics to reach iTerm, BOTH the inner `tmux-256color` AND the outer terminal's
entry must have `sitm`. If the outer entry lacks it, tmux drops the italics.

## The old problem (CentOS 7/8 era) -- now obsolete

My mac's iTerm sets `TERM=xterm-256color`. Years ago the devserver's
`xterm-256color` terminfo was outdated and lacked `sitm`, so:
- screen-256color (tmux's old default): no italics.
- xterm-256color: the mac and devserver "agreed" on the name, but the devserver's
  definition was stale and had no italics, so tmux dropped them.
- tmux-256color: this one DID have italics on the devserver.

So I hacked around it by forcing `TERM=tmux-256color` at ssh-time (in
bin/ssh_command.py). That lies about the terminal type, but it got me italics.

This whole saga traces back to colinchan's `fb-terminfo-backports`
(D18530862 / D19894434, 2019-2020): CentOS 8's ncurses-6.1 definitions used
`pairs#0x10000`, incompatible with platform007's ncurses-5.9 (`pairs#0x7fff`),
so a backport package shipped fixed defs via `TERMINFO_DIRS`. See the $TERM wiki:
https://www.internalfb.com/wiki/Development_Environment/%24TERM/

## The actual root cause (today) and the real fix

The devserver is now **CentOS Stream 9 with ncurses 6.2**. Its system
`/usr/share/terminfo/x/xterm-256color` is modern and DOES have italics
(`sitm=\E[3m`, `ritm`, `smxx`, `pairs#0x10000`). `fb-terminfo-backports` is not
even installed -- CentOS 9 doesn't need it.

The thing still breaking italics under `xterm-256color` was **my own
`~/.terminfo`**: a stale hand-installed `x/xterm-256color` (and
`s/screen-256color`) left over from the old era. It had NO `sitm` and the old
`pairs#0x7fff`. Because `~/.terminfo` is first in ncurses' search path, it
*shadowed* the good system entry. So `xterm-256color` resolved to my crippled
copy -> no italics -> I "needed" the tmux-256color override.

The proper fix, with no ssh-time TERM override:

1. **Delete the stale shadow** so xterm-256color resolves to the system entry:
   ```
   rm -rf ~/.terminfo        # the system ncurses-6.2 defs are strictly better
   ```
   Verify on any host: `infocmp -x xterm-256color | grep -c sitm`  # expect 1
2. **Don't override TERM at ssh-time.** Let iTerm's real `xterm-256color` pass
   through (removed from bin/ssh_command.py).
3. **Keep** `set -g default-terminal "tmux-256color"` in tmux.conf (correct).
4. **Truecolor through tmux:** add `set -as terminal-features ",xterm-256color:RGB"`
   to tmux.conf. (I also export `COLORTERM=truecolor`, which mostly covers it.)

Net: TERM is honest end-to-end, and both italics and truecolor work inside and
outside tmux -- on any modern (ncurses-6.x) host, with no per-host hacks.
