# .bash_aliases

alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias ls='ls --color=auto'

alias vimr='vim -R'
alias cd='cd -P'
alias ig='egrep -ns --colour=auto'
alias clear='for qwedc in {1..100} ; do echo " " ; done ; clear'
alias freq='sort | uniq -c | sort -nr'
alias l='echo "`whoami` `hostname` `pwd`"'

function mkcd {
    mkdir -p "$1" && cd "$1"
}
