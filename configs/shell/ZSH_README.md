# Zsh configuration

Two parts:

- **Part 1 — how zsh's startup files work in general.** A self-contained
  explainer of `.zshenv`, `.zprofile`, `.zshrc`, `.zlogin`, `.zlogout`: when each
  is read and what belongs in it.
- **Part 2 — how this repo wires into that model**, file by file.

---

# Part 1 — How the zsh startup files work (general)

Zsh reads up to five user files at startup. Which ones it reads, and in what
order, depends on **what kind of shell** is starting. That classification is the
whole key — the filenames only make sense once you know the two axes.

## The two axes: login vs. interactive

Every shell instance has two independent boolean properties:

- **Login shell** — the shell started as part of *logging in* (SSH session, a
  console TTY login, `su -`, or a top-level shell spawned with `-l`). It's the
  first shell of a session, responsible for setting up the environment for
  everything beneath it.
- **Interactive shell** — a human is typing at a prompt. Contrast with a
  *non-interactive* shell, which runs a script and exits (`zsh script.sh`,
  `zsh -c 'cmd'`, or a command run over SSH like `ssh host 'cmd'`).

These combine into four cases:

|                  | Interactive                       | Non-interactive                 |
| ---------------- | --------------------------------- | ------------------------------- |
| **Login**        | SSH login, console login, `zsh -l`| `zsh -l -c 'cmd'`, login script |
| **Non-login**    | new terminal tab, `zsh`, tmux pane| `zsh script.sh`, `zsh -c 'cmd'` |

## The files and their order

The files live in `$ZDOTDIR` (defaults to `$HOME` if unset). They are sourced in
this **fixed order**, but each is gated on the shell type:

```
                      ALWAYS    if LOGIN   if INTERACTIVE   if LOGIN
                         │          │            │             │
  .zshenv  ──────────────┘          │            │             │
  .zprofile ────────────────────────┘            │             │   (login only)
  .zshrc  ───────────────────────────────────────┘             │
  .zlogin ─────────────────────────────────────────────────────┘   (login only)
```

Precisely:

1. **`.zshenv`** — sourced for **every** shell, always. No conditions.
2. **`.zprofile`** — sourced for **login** shells, *before* `.zshrc`.
3. **`.zshrc`** — sourced for **interactive** shells.
4. **`.zlogin`** — sourced for **login** shells, *after* `.zshrc`.
5. **`.zlogout`** — sourced when a **login** shell *exits* (not at startup).

So `.zprofile` and `.zlogin` bracket `.zshrc`: profile before, login after.
They're two slots for login-only logic — one that runs before your interactive
config, one after.

There are also **system-wide** counterparts in `/etc` (`/etc/zshenv`,
`/etc/zprofile`, `/etc/zshrc`, `/etc/zlogin`, `/etc/zlogout`), each sourced
immediately *before* the corresponding user file. `/etc/zshenv` is always read
first of all and cannot be suppressed.

## Worked examples

- **SSH into a box** (login + interactive): `zshenv` → `zprofile` → `zshrc` →
  `zlogin`. On logout: `zlogout`.
- **Open a new terminal tab** (typically non-login + interactive): `zshenv` →
  `zshrc`. (macOS Terminal.app is the famous exception — it runs login shells, so
  it also reads `zprofile`/`zlogin`.)
- **tmux pane / typing `zsh`** (non-login + interactive): `zshenv` → `zshrc`.
- **Run a script** `zsh deploy.sh` (non-login + non-interactive): `zshenv`
  **only**.
- **`ssh host 'echo hi'`** (non-login + non-interactive): `zshenv` only.

That last pair is the practical reason `.zshenv` matters: it is the *only* file
guaranteed to run for non-interactive, non-login invocations.

## What belongs in each — and why

### `.zshenv` — environment for *everything*
Runs always, so it holds what every shell (including scripts and
`ssh host cmd`) needs:
- `PATH` and other exported environment variables that non-interactive tools
  depend on.
- `ZDOTDIR` itself, if you relocate your config (must be set here — it's the only
  always-read file).

**Caveats:** keep it lean and side-effect-free. It runs for *every* zsh, so
anything slow or anything that prints output will break scp/rsync/scripts. Don't
put aliases, prompt, or terminal escapes here. (Bash users coming to zsh often
trip on this: bash's non-interactive remote-command path doesn't read a profile
at all by default, whereas zsh's `.zshenv` does.)

### `.zprofile` — login-time setup, *before* interactive config
Runs once per login, before `.zshrc`. Mirrors bash's `.profile`/`.bash_profile`.
Use for:
- One-time-per-session environment setup that should be inherited by all
  sub-shells.
- Commands you want evaluated at login (e.g. `eval "$(brew shellenv)"` on macOS).

Since it runs before `.zshrc`, values it sets can be used/overridden there.

### `.zshrc` — interactive shell configuration
The workhorse, where most config goes. Runs for every interactive shell. Use
for:
- Aliases and shell functions.
- Prompt (`PROMPT`/`RPROMPT`), themes.
- Keybindings (`bindkey`), completion (`compinit`, `zstyle`), history options
  (`HISTSIZE`, `setopt`).
- Anything that only makes sense when a human is typing.

Because it runs for *every* interactive shell — not just login ones — nested
shells and new tabs all get it.

### `.zlogin` — login-time setup, *after* interactive config
Same gating as `.zprofile` (login shells) but runs *after* `.zshrc`. Use it when
something should happen at login *after* the interactive environment is fully
built:
- Launching a startup command, printing a fortune/MOTD, starting a
  session-level process.

`.zprofile` vs `.zlogin` is mostly timing relative to `.zshrc`. If you don't need
to run *after* `.zshrc`, prefer `.zprofile`.

### `.zlogout` — login shell teardown
Runs when a **login** shell exits cleanly. Use for:
- Cleanup (clearing the screen, removing temp files, stopping a process started
  in `.zlogin`).
- Logging session end.

It's login-only — exiting a non-login interactive subshell does *not* trigger it.

## Mental model

- **`.zshenv`**: always. Environment variables. Keep it silent and fast.
- **`.zprofile`**: login, before rc. Bash-`.profile`-style setup.
- **`.zshrc`**: interactive. Aliases, prompt, keybindings, completion.
- **`.zlogin`**: login, after rc. Startup actions needing the full interactive env.
- **`.zlogout`**: login exit. Cleanup.

Rule of thumb for *where to put a thing*:
1. Needs to be visible to scripts / `ssh host cmd` / GUI apps? → **`.zshenv`** (export it).
2. It's an alias, prompt, completion, or keybinding? → **`.zshrc`**.
3. It's a once-per-login action? → **`.zprofile`** (before rc) or **`.zlogin`** (after rc).
4. It's session teardown? → **`.zlogout`**.

A common gotcha: if `PATH` set in `.zshrc` seems to "not apply" in scripts or
cron, that's expected — `.zshrc` doesn't run for non-interactive shells. Move the
export to `.zshenv`.
