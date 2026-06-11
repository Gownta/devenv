# Bash support (removed)

This repo no longer ships a bash profile. `configs/shell/profile.bash` was
deleted because the shell config migrated to zsh-only PATH handling (zsh arrays
+ `typeset -U` in `configs/shell/env`), which bash cannot parse.

## Recovering profile.bash

The last commit that contained `configs/shell/profile.bash` is:

    44fe6934ba7a14a7615b2992c4821c8c5a185ca1   ("use zsh-style path updating")

GitHub:
- Commit: https://github.com/Gownta/devenv/commit/44fe6934ba7a14a7615b2992c4821c8c5a185ca1
- File at that commit: https://github.com/Gownta/devenv/blob/44fe6934ba7a14a7615b2992c4821c8c5a185ca1/configs/shell/profile.bash

To view or restore it locally:

    # view its contents
    git show 44fe693:configs/shell/profile.bash

    # restore it into the working tree
    git checkout 44fe693 -- configs/shell/profile.bash

## Defaulting to zsh

`zsh` is installed at `/usr/bin/zsh` (also `/bin/zsh`) and is listed in
`/etc/shells`.

Set zsh as your login shell:

    chsh -s /bin/zsh

Then log out and back in. Verify:

    echo "$SHELL"            # -> /bin/zsh
    getent passwd "$USER"    # last field -> /bin/zsh

### If `chsh` doesn't stick (managed / provisioned hosts)

Some managed hosts reset the passwd shell on reprovision. As a fallback, hand
off from bash to zsh in bash's startup. Add to `~/.bash_profile` (login) or
`~/.bashrc` (interactive):

    # Hand off to zsh if available and we're an interactive bash
    if [ -z "$ZSH_VERSION" ] && [ -x /bin/zsh ] && [[ $- == *i* ]]; then
      exec /bin/zsh -l
    fi

The `[[ $- == *i* ]]` guard keeps non-interactive bash (scripts, `ssh host cmd`)
from being hijacked.

### Note

`envs/devserver/bashrc` still sources `configs/shell/profile.bash`. With the
file gone, that line errors if interactive bash is ever launched. Drop that
`source` line for a clean bash startup, or ignore it — once your login shell is
zsh, that bashrc isn't sourced anyway.
