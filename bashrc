# .bashrc

################################################################################
### Facebook stuff

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

################################################################################
### History

# don't put duplicate lines in the history. See bash(1) for more options
# ... or force ignoredups and ignorespace
HISTCONTROL=ignoredups:ignorespace

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=20000
HISTFILESIZE=50000

# set history time format to "YYYYMMDD - HH:MM:SS [command]"
export HISTTIMEFORMAT="[ %y/%m/%d - %H:%M:%S ]  "

# Ignore certain commands in history
export HISTIGNORE="ls:cd ..:pwd:hostname"

################################################################################
### Appearance

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# change prompt to " > "
export PS1=" > "

#echo "
#    _   ___      __          __              ____                                __
#   / | / (_)____/ /_  ____  / /___ ______   / __ \_________ ___  _________  ____/ /
#  /  |/ / / ___/ __ \/ __ \/ / __ \`/ ___/  / / / / ___/ __ \`__ \/ ___/ __ \/ __  /
# / /|  / / /__/ / / / /_/ / / /_/ (__  )  / /_/ / /  / / / / / / /  / /_/ / /_/ /
#/_/ |_/_/\___/_/ /_/\____/_/\__,_/____/   \____/_/  /_/ /_/ /_/_/   \____/\__,_/
#"

################################################################################
### Handy

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
    . /etc/bash_completion
fi


################################################################################
### Aliases

alias vimr='vim -R'
alias cd='cd -P'
alias ig='egrep -ns --colour=auto'
alias clear='for qwedc in {1..100} ; do echo " " ; done ; clear'
alias freq='sort | uniq -c | sort -nr'

################################################################################
### Variables

export EDITOR=/usr/bin/vim
