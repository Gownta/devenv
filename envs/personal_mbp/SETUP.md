From internet, install chrome, textmate, iterm
textmate: https://macromates.com/
sign in to google
sign into my password manager

Install git...
xcode-select --install

in .ssh/: ssh-keygen -t ed25519 -C "nicholas.ormrod@gmail.com"
PASSWORD TO PMBP. lastpass > github
in github, add the new key
git clone git@github.com:Gownta/devenv.git
also lexemes, tmux-power, and phoenix
Add the new ssh key to ~/.ssh/authorized_keys in my AWS EC2 instance

In settings,
invert scrolling
hot corners
dark mode was done during computer setup
keyboard > rebind caps lock to escape

ln -s gitconfig, tmux.conf, vimrc, zshrc, zshenv

Install Nerd Font "Noto", unzipped into ~/Library/Fonts
https://www.nerdfonts.com/

Load my iterm config
Needed to go to settings > keys > navigation shortcuts, and therein, disable the shortcut to change tabs, since that was interfering with my cmd-N tmux switch overrides
Change font size in iterm to 16. 11 is too small
Change font to Nerd Noto Mono

Used homebrew to install tmux

Install Claude Code:
(instructions: https://claude.ai/code/family)
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew

Sigh... I installed homebrew:
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

/opt/homebrew/bin/brew install tmux

But I didn't do the next steps...

It says to add these to my zprofile:
export HOMEBREW_PREFIX="/opt/homebrew";
export HOMEBREW_CELLAR="/opt/homebrew/Cellar";
export HOMEBREW_REPOSITORY="/opt/homebrew";
eval "$(/usr/bin/env PATH_HELPER_ROOT="/opt/homebrew" /usr/libexec/path_helper -s)"
[ -z "${MANPATH-}" ] || export MANPATH=":${MANPATH#:}";
export INFOPATH="/opt/homebrew/share/info:${INFOPATH:-}";

I want to add:
export HOMEBREW_NO_AUTO_UPDATE=1


