# .bash_aliases

alias qq="source ~/.bash_profile"

alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias ls='ls --color=auto'

alias vimr='vim -R'
alias cd='cd -P'
alias clear='for qwedc in {1..100} ; do echo " " ; done ; clear'
alias freq='sort | uniq -c | sort -nr'

alias f1="awk '{print \$1}'"
alias f2="awk '{print \$2}'"
alias f3="awk '{print \$3}'"
alias f4="awk '{print \$4}'"
alias f5="awk '{print \$5}'"
alias f6="awk '{print \$6}'"
alias f7="awk '{print \$7}'"
alias f8="awk '{print \$8}'"
alias f9="awk '{print \$9}'"

function mkcd {
    mkdir -p "$1" && cd "$1"
}
