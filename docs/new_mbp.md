# New Mac

To set up a new laptop:

Download:
- Chrome
- iTerm2

git clone this devenv repo. symlinkify. Notes:
- `git clone git@github.com:Gownta/devenv.git`
- .zshenv -> configs/shell/env
- create ~/.secrets, add `# export EXAMPLE_SECRET=12345`
- create ~/.tmux.panes, containing 6 blank lines

Add an ssh key in github
- `~/.ssh$ ssh-keygen -t ed25519 -C "nicholas.ormrod+github@gmail.com"`
- Github.com > Settings > New SSH Key
Add the key to ssh-agent
- `ssh-agent`
- `ssh-add ~/.ssh/id_ed25519`
Github (cont'd)
- git push to verify

System Settings
- Set Appearance to Dark Mode
- Undo inverse mouse
- Set default browser to chrome
