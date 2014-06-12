# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# User specific environment and startup programs

#echo "
#    _   ___      __          __              ____                                __
#   / | / (_)____/ /_  ____  / /___ ______   / __ \_________ ___  _________  ____/ /
#  /  |/ / / ___/ __ \/ __ \/ / __ \`/ ___/  / / / / ___/ __ \`__ \/ ___/ __ \/ __  /
# / /|  / / /__/ / / / /_/ / / /_/ (__  )  / /_/ / /  / / / / / / /  / /_/ / /_/ /
#/_/ |_/_/\___/_/ /_/\____/_/\__,_/____/   \____/_/  /_/ /_/ /_/_/   \____/\__,_/
#"

PATH=$PATH:$HOME/dev/bin

shopt -s checkwinsize

export PATH
unset USERNAME

# Record unusual exit statuses in command prompt
function ipromptcmd () {
  local stat="$?"
  if [[ "$stat" -ne 0 ]] ; then
    #local signal="$(builtin kill -l $[$stat - 128] 2>/dev/null)"
    #test "$signal" && signal=" ($signal)"
    echo "[Exit $stat]" 1>&2
  fi

  # Log lines immediately, not just at session termination
  history -a

  return 0
}
export PROMPT_COMMAND=ipromptcmd

# when autocompleting in the 'cd' command, only consider directories
complete -d cd
