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

---

# Part 2 — How this repo wires into that model

`ansible/fixmyserver.yaml` symlinks the home dotfiles to files in this repo, and
`ansible/setup_user.yaml` sets the login shell to `/bin/zsh`:

```
~/.zshenv      ->  configs/shell/env           # always; env + PATH
~/.zshrc       ->  configs/shell/zshrc         # interactive; loads everything
~/.env_profile ->  envs/<host>/env_profile     # per-host env, maybe_source'd by zshrc
```

`.zprofile`, `.zlogin`, and `.zlogout` are not symlinked, so zsh skips them —
unless you opt into the per-host `envs/<host>/` bundle (below).

Load chain for an interactive login shell:

```
.zshenv  (= configs/shell/env)            ALWAYS — runs first
    └─ NJORMROD_DEVENV, PATH (typeset -U array), RUSTUP/CARGO, EDITOR, colors…

.zshrc   (= configs/shell/zshrc)          INTERACTIVE
    ├─ source configs/shell/profile           # generic (zsh + bash)
    │     ├─ source configs/shell/env          # AGAIN — idempotent; see note
    │     ├─ source configs/shell/aliases
    │     ├─ source configs/shell/functions
    │     ├─ cursor, ssh-agent, ENVRCDIR → $ENVRCDIR/envrc, OnDemand hgrc patch
    ├─ source configs/shell/profile.zsh       # zsh-only: keybinds, compinit, prompt
    └─ maybe_source ~/.env_profile            # per-host env

.zlogin                                   LOGIN — none by default
```

**Note — `env` runs twice.** `configs/shell/env` is both `~/.zshenv` *and* is
sourced again by `profile` (so bash, which has no `.zshenv`, still gets the
environment). Re-running is safe by design: `PATH` uses `typeset -U` (dedups on
every run) and everything else is plain idempotent `export`s.

### Per-host variant (`envs/<host>/`)

Per the top-level README's setup step, instead of the generic files you can
symlink a host bundle. `envs/<host>/zshrc` sets `ENVRCDIR` and then sources the
same `profile` + `profile.zsh`; `envs/<host>/zlogin` is the login slot (banner
art + `ssh_command.py`, and returns early inside tmux / over SSH).

## File-by-file (this repo)

### `configs/shell/env`  →  `~/.zshenv`
- **When:** every zsh — interactive *and* not (scripts, `ssh host cmd`, tmux
  panes, subshells) — plus again via `profile`.
- **Put here:** exported environment that non-interactive things also need:
  `PATH` (the `typeset -U; path=(…)` array), `NJORMROD_DEVENV`, `EDITOR`,
  `RUSTUP_HOME`/`CARGO_HOME`, color vars.
- **Keep out:** aliases, prompt, keybindings, anything interactive, and anything
  that prints output (stray output breaks scp/rsync/non-interactive ssh). Keep it
  fast and silent, and idempotent — it runs many times per session.
- This is the repo's `.zshenv` (Part 1).

### `configs/shell/zshrc`  →  `~/.zshrc`
- **When:** every interactive zsh.
- **Role:** thin loader — sources `profile`, then `profile.zsh`, then
  `~/.env_profile`. Add new interactive includes here. This is the repo's
  `.zshrc` (Part 1).

### `configs/shell/profile`  (generic — zsh and, historically, bash)
- **When:** every interactive shell, via `zshrc`.
- **Put here:** shell-agnostic interactive setup that must work in *both* zsh and
  bash — generic includes (`env`/`aliases`/`functions`), ssh-agent bootstrap,
  `ENVRCDIR` detection, cursor, host hooks. **POSIX-ish syntax only** — no zsh
  arrays or `typeset -U`.

### `configs/shell/profile.zsh`  (zsh-only)
- **When:** every interactive zsh, via `zshrc`.
- **Put here:** the zsh-specific interactive config that Part 1 lists under
  `.zshrc` — `bindkey`, `setopt`, `compinit`, the prompt (`precmd`/`preexec`,
  `PROMPT`), `zstyle`.

### `configs/shell/aliases`  /  `configs/shell/functions`
- **When:** via `profile`, so every interactive shell.
- **Put here:** aliases and shell functions. Keep them portable.

### `configs/shell/envrc`  →  loaded as `$ENVRCDIR/envrc` (or `~/.envrc`)
- **When:** via `profile`'s ENVRCDIR / `maybe_source` logic.
- **Put here:** prompt variables and per-environment cosmetics (icons,
  `PROMPT_VAR_*`). The active file is `$ENVRCDIR/envrc`, chosen per host.

### `envs/<host>/env_profile`  →  `~/.env_profile`
- **When:** end of `zshrc` (`maybe_source`).
- **Put here:** per-host environment overrides.

### `envs/<host>/zshrc`, `envs/<host>/zlogin`  (per-host bundle)
- **When:** only if you symlink these instead of the generic files.
- `zshrc`: sets `ENVRCDIR`, then loads `profile` + `profile.zsh`.
- `zlogin`: the repo's only use of the **`.zlogin`** slot (Part 1) — login-only
  banner art (skipped over SSH) and `ssh_command.py`; returns early inside tmux.

### Not used here: `.zprofile`, `.zlogout`
See Part 1 for what these are for. Neither is symlinked; add one if you need
login-time env *before* `.zshrc` (`.zprofile`) or logout cleanup (`.zlogout`).

## Where do I put …?

| I want to add…                                   | File |
| ------------------------------------------------ | ---- |
| An env var that scripts / `ssh host cmd` need    | `env` (export it) |
| A `PATH` entry                                   | `env`, in the `path=(…)` array |
| An alias or shell function                       | `aliases` / `functions` |
| A keybinding, completion, or prompt tweak        | `profile.zsh` |
| Interactive setup that must also work in bash    | `profile` |
| Prompt icons / per-environment cosmetics         | `envrc` |
| A per-host override                              | `envs/<host>/env_profile` (or that host's bundle) |
| A one-time login action (banner, greeting)       | `envs/<host>/zlogin` (login-only) |

**Rule of thumb:** non-interactive-safe env → `env`; interactive zsh-only →
`profile.zsh`; cross-shell interactive → `profile`.
