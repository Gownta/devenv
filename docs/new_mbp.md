# New Mac

To set up a new laptop:

Download:
- Chrome
- iTerm2
  - I have iTerm config in devenv
- Outlook
- Nerd Font https://www.nerdfonts.com/
  - Once downloaded, copy unzipped directory to ~/Library/Fonts
  - Noto, Hack, Cousine

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
- Keyboard > Keyboard Shortcuts > Modifier Keys
    1. Select Keyboard
    2. Caps Lock -> Esc

Homebrew
- work mbp: https://fb.workplace.com/groups/hack.of.the.day/permalink/1925865110834868/
- personal: ??

...then some brew things
- brew install tmux

Connect to wifi
- lighthouse
- metaguest?
- home wifi

Order a new laptop decal, gelaskins.com

Set up dropbox.
- Install dropbox
- Download the backup folder
- Copy contents to Desktop, etc
- Set up new backup for my desktop

Install some other apps:
- TextMate
- Discord
- Unity
- Android Studio
