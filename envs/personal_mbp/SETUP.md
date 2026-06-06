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

In settings,
invert scrolling
hot corners

ln -s gitconfig, tmux.conf, vimrc, zshrc, zshenv

Load my iterm config
Change font size. It's too small


# Homebrew

Sigh... I installed homebrew:
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

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


