# .bashrc

################################################################################
# History

shopt -s histappend
HISTCONTROL=ignoredups:ignorespace
HISTSIZE=20000
HISTFILESIZE=50000
export HISTTIMEFORMAT="[ %y/%m/%d - %H:%M:%S ]  "
export HISTIGNORE="ls:cd ..:pwd:hostname"
