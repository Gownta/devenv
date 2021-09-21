# bash_aliases

# Default options on common commands
alias grep='grep --color=auto -s'
alias fgrep='fgrep --color=auto -s'
alias egrep='egrep --color=auto -s'
alias ls='ls --color=auto'
alias cd='cd -P'

# Shorthand
alias c='clear'
alias v='vim'
alias codemod="/data/users/njormrod/repos/www/scripts/bin/codemod --extensions='*'"
alias qq="source ~/.bash_profile"

# New commands
alias clear='for qwedc in {1..100} ; do echo " " ; done ; clear'
alias freq='sort | uniq -c | sort -nr'
alias vimr='vim -R'

alias bcp='b contextprop/cpp/...'
alias tcp='b t contextprop/cpp/...'
alias njor='b r scripts/njormrod/tmp:main'
alias t='c;b t'
alias b="c;b"

# Indexing shorthand
alias f1="awk '{print \$1}'"
alias f2="awk '{print \$2}'"
alias f3="awk '{print \$3}'"
alias f4="awk '{print \$4}'"
alias f5="awk '{print \$5}'"
alias f6="awk '{print \$6}'"
alias f7="awk '{print \$7}'"
alias f8="awk '{print \$8}'"
alias f9="awk '{print \$9}'"

alias c1="cd ~/repos/1fbsource/fbcode"
alias c2="cd ~/repos/2fbsource/fbcode"
alias c3="cd ~/repos/3fbsource/fbcode"
alias c4="cd ~/repos/4fbsource/fbcode"
alias c5="cd ~/repos/5fbsource/fbcode"
alias c6="cd ~/repos/6configerator/source"

function mkcd {
    mkdir -p "$1" && cd "$1"
}

function cr {
    cd `hg root`/fbcode
}

function ccp {
    cd `hg root`/fbcode/contextprop/cpp
}

function cf {
    cd $(dirname $1)
}

function cnjo {
    cd `hg root`/fbcode/scripts/njormrod
}
