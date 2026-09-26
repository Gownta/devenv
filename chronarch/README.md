# Chronarch

Chronarch is an AI cron engine.

Crons are stored in spec/ directories.
The engine/ reads and executes the crons in spec/.
  src/ and test/ subdirs
Runtime information is stored in `$CHRONARCH_ROOT`.
Defaults are stored in ./config.toml.
Executable ./rr function that invokes the engine.


## Spec

Any (recursive) subdirectory of spec/ that contains info.toml is a cron spec root.

The name of a cron spec is the relative path between spec/ and info.toml. spec/foo/bar/info.toml is the foo/bar cron. Crons cannot be nested; foo/bar precludes foo/bar/part.

Spec dirs are searched in order, like `$PATH`:
1. the local spec/ (`spec_dir` in config.toml), unless `--no-local-specdir`
2. `$CHRONARCH_SPECDIRS`, colon-separated
3. each `--specdir DIR`

If two spec dirs define the same cron name, the first one wins; the shadowed cron is logged and ignored.

info.toml contains:
- `description`, a string explanation of what the cron does
- `schedule`, either a string or a list of strings. Each string is a systemd calendar spec.
- `exe`, the file to execute
  - relative paths are relative to the spec root
  - .md files are invoked as AI commands
  - Other files are executed

and may optionally include:
- `[ai]`
  - `provider` (claude or codex, default taken from config.toml)
  - `model` (default taken from config.toml)
  - `effort` (default taken from config.toml)
- `[process]`
  - `timeout_s` (defaulted in config.toml)
  - `root_dir`
  - `max_concurrent` (defaults to 1)


## Runtime info

Each cron gets a directory according to its name, in `$CHRONARCH_ROOT/rundirs/`
Therein, there is:
- `_lockfile.flock`, acquired when the cron is initiating, released when the cron finishes (except for concurrent crons)
- runs/, containing directories of the form `YYYY_MM_DD__HH_MM_SS__ID`, where ID starts at 0 and increments for each successive cron run at that exact second.
  - meta.toml
    - `start_time`, human-readable string
    - `end_time`
    - `max_duration_s`, how many seconds before the process should be killed
    - `duration`, human-readable time, like `3m17s`. d,h,m,s; show at most two (so never 2h14m34s), second has two digits (so 1m03s instead of 1m3s), round up (so 1s instead of 0s)
    - `duration_s`, float, 3 decimal places
    - `pid`, of the primary process
    - `exit_code`
    - `kill_reason` (not present for normally-exited processes) (timeout, cancelled)
  - stdout.txt (written by the subprocess)
  - stderr.txt (written by the subprocess)
- latest/, a symlink pointing to the latest run dir.

Note: as much of meta.toml is written before the process starts as possible. Immediately after starting, the pid is appended to meta.toml. Other fields are appended afterwards.

The run dir is created before the process starts, and is passed into the cron as the environment variable `$CHRONARCH_RUNDIR`.


## Engine

Python, argparse.

Subcommands:
- drive; is the engine that schedules crons
  - logs to stdout whenever a cron is scheduled. Minimalist: time, cron name, pid
- run CRONNAME; triggers execution of a specific cron
- kill CRONNAME; stops a specific cronjob


There is a sqlite db at `$CHRONARCH_ROOT/db`.

Table `active_runs` tracks the cron name, rundir, pid, and `kill_ts` of actively-running crons. This is especially useful when restarting the engine. Subprocesses launched by the engine have a callback; orphaned and reclaimed pids are checked every minute and killed if their kill-ts is reached.

There is a log file at `$CHRONARCH_ROOT/logs`.


## Usage

```
./rr drive          # run forever (e.g. under a systemd user service)
./rr run foo/bar    # run a cron now, in the foreground; exits with its exit code (128+N if killed by signal N)
./rr kill foo/bar   # cancel all active runs of a cron
./rr --config other.toml ...
./rr --specdir ~/more/spec --no-local-specdir drive
```

Ctrl-C or SIGTERM on `./rr run` cancels the run.

Tests: `python3 -m unittest discover -s engine/test`

Requires python >= 3.11, or `tomli` on older pythons, and `systemd-analyze`, which evaluates the calendar specs (in local time).

`$CHRONARCH_ROOT` falls back to `root` in config.toml.
Besides `$CHRONARCH_RUNDIR`, crons also get `$CHRONARCH_CRON` (their name) and `$CHRONARCH_ROOT`.
AI crons get their .md file on stdin: `claude -p` or `codex exec -`, plus the provider's `args` from config.toml.
`root_dir` (relative to the spec root) is the working directory; it defaults to the spec root.


## Implementation notes

- Each run is its own session/process group; kills send SIGTERM to the group, then SIGKILL after `kill_grace_s`.
- `exit_code` is negative when the process died from a signal (-15 is SIGTERM). A run that fails to start gets `exit_code = 127` and an `error`.
- Runs outlive the engine process that started them. If that process dies, the run is orphaned: `drive` kills it at `kill_ts` and finalizes its meta.toml once it exits, but its exit code is lost (meta.toml gets a `note` instead).
- The lock on `_lockfile.flock` dies with its engine process, so the concurrency check also counts live runs in `active_runs`.
- Schedules that pass while `drive` is down are not caught up.
