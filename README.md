DevEnv
======

# Setup

1. Clone this repo
2. Determine which configs should be used, from configs/ and/or envs/, and symlink them from ~.
3. Follow steps in the README to configure additional things.

Optionally:
- Create a ~/.secrets file containing things that should not be committed to source control (eg `OPENAI_API_KEY`, `METAGEN_KEY`)
- Create ~/.tmux.panes, one line per window, each line optionally containing a directory
- Add an ssh key in github
  eg command: `~/.ssh$ ssh-keygen -t ed25519 -C "nicholas.ormrod+github@gmail.com"`


Debugging
=========

Connecting to github is hard on a devserver. See this wiki page for info: [page](https://www.internalfb.com/intern/wiki/Open_Source/Maintain_a_FB_OSS_Project/Devserver_GitHub_Access/)


Organization
============

bin/
  Contains developer environment binaries
configs/
  Contains configuration files for various applications
envs/
  Contains specifications for specific environments
originals/
  Dotfiles that were on the system beforehand; gitignored


Notes
=====

1. Configuring iTerm2 and tmux

I want to send hex codes to tmux using iterm keyboard shortcuts.
In profile>keys, override command-[number] to Send Hex Code 0x02 0x3[number].
Also need to remove command-number override in general>keys>navigation shortcuts
Also add command-` to 0x02 0x3b, which is 'ctrl-b ;', which changes panes
Also add cmd-hjkl to be tmux commands for hjkl
Also add cmd-shift-right|left to navigate iterm tabs (prev and next tab)


2. devservers

To clone from FBDev: git clone ssh://git@github.com/Gownta/dotfiles
                     (this is the SSH url provided on github.com)
To commit from FBDev: generate an access token from Seetings > Applications
                      use this token as my password
                      git push origin master

Getting the repo on a devserver
  - https://www.internalfb.com/intern/wiki/Open_Source/Maintain_a_FB_OSS_Project/Devserver_GitHub_Access/
  - Start with git pull
  - git push origin master when done commits
  - use save_and_set_home_dotfiles to set devserver dotfiles
    - will save originals in originals/


Things to install
=================

Not dotfiles, but stuff that I also set up on new machines:

Mosh
  mbp > Managed Software Center > Mosh
Bazel
  https://docs.bazel.build
  --prefix=$HOME/dev/bazel, instead of --use
