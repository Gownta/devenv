# .bash_aliases

alias grep='grep --color=auto -s'
alias fgrep='fgrep --color=auto -s'
alias egrep='egrep --color=auto -s'
alias ls='ls --color=auto'
alias g='grep -Es --color=auto'

alias vimr='vim -R'
alias cd='cd -P'
alias ig='egrep -ns --colour=auto'
alias clear='for qwedc in {1..100} ; do echo " " ; done ; clear'
alias freq='sort | uniq -c | sort -nr'
#alias l='echo "`whoami` `hostname` `pwd`"'

alias bbr='b admarket/up2x/reader:up2x_reader_server'
alias bbw='b admarket/up2x/writer:up2x_writer_server'
alias bbu='b admarket/up2x/reader:up2x_reader_server admarket/up2x/writer:up2x_writer_server admarket/up2x/util:loadtest2x admarket/up2x/util:lookup_shard admarket/up2x/util:open_segment_file'
alias bbe='b experimental/njormrod/tmp:test'

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
alias cr="cd `hg root`/fbcode"

alias dce=~/dev/dce/dce_candidate.sh
alias codemod="codemod --extensions='*'"
alias qq="source ~/.bash_profile"

function mkcd {
    mkdir -p "$1" && cd "$1"
}

function cdfbc {
    cd `hg root`/fbcode
}

function cf {
    cd $(dirname $1)
}
