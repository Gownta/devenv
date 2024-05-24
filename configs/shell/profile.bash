# bash-specific profile

# Command edit mode
set -o vi

# History
shopt -s histappend
HISTCONTROL=ignoredups:ignorespace
HISTSIZE=20000
HISTFILESIZE=50000
export HISTTIMEFORMAT="[ %y/%m/%d - %H:%M:%S ]  "
export HISTIGNORE="ls:cd ..:pwd:hostname"

# etc/
maybe_source /etc/bashrc
maybe_source /etc/bash_completion

# Misc
shopt -s checkwinsize
complete -d cd

################################################################################
# Prompt

# Record unusual exit statuses in command prompt
# Log lines immediately, not just at session termination

function ips1cmd() {
  echo $PWD | \
      sed 's,/home/njormrod,~,' | \
      sed 's,/data/users/njormrod,local,' | \
      sed 's,local/repos,r,' | \
      sed 's,^r/\([0-9]\)*configerator/source,r/\1cfg/s,' | \
      sed 's,^r/\([0-9]\)*configerator,r/\1cfg,' | \
      sed 's,\([0-9]\)fbsource/fbcode,\1f,'
}

function ipromptcmd () {
  local stat="$?"
  if [[ "$stat" -ne 0 ]] ; then
    echo -e "\033[1;91m[Exit $stat]\033[0m" 1>&2
  fi

  history -a

  return 0
}
export PROMPT_COMMAND=ipromptcmd
export PS1='\[\033[1;96m\]\T $(ips1cmd) \$\[\033[0m\] '
