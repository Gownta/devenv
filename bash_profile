# bash_profile

################################################################################
# call out to other sources

bash_source_callout () {
  if [ -f $1 ] ; then . $1 ; fi
}

bash_source_callout /etc/bash_completion
bash_source_callout ~/.bashrc


################################################################################
# ascii name

# generated on http://patorjk.com/software/taag
# ascii art font: slant
# note: the terminal must have an appropriate font, like Courier
# run only once per terminal window, i.e. do not run on ssh

if [ -z "$SSH_CONNECTION" ] ; then
echo '
    _   ___      __          __              ____                                __
   / | / (_)____/ /_  ____  / /___ ______   / __ \_________ ___  _________  ____/ /
  /  |/ / / ___/ __ \/ __ \/ / __ `/ ___/  / / / / ___/ __ `__ \/ ___/ __ \/ __  /
 / /|  / / /__/ / / / /_/ / / /_/ (__  )  / /_/ / /  / / / / / / /  / /_/ / /_/ /
/_/ |_/_/\___/_/ /_/\____/_/\__,_/____/   \____/_/  /_/ /_/ /_/_/   \____/\__,_/
'
fi


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
  color=
  if [[ "$stat" -ne 0 ]] ; then
    echo -e "\033[1;91m[Exit $stat]\033[0m" 1>&2
  fi

  history -a

  return 0
}
export PROMPT_COMMAND=ipromptcmd
export PS1='\[\033[1;96m\]\T $(ips1cmd) \$\[\033[0m\] '
if [[ `hostname` == "devvm7450.prn2.facebook.com" ]] ; then
  export PS1='\[\033[1;95m\]\T $(ips1cmd) \$\[\033[0m\] '
fi


################################################################################
# Miscellaneous

shopt -s checkwinsize
complete -d cd

################################################################################
# Keychain

# sudo apt-get insall keychain
/usr/bin/keychain $HOME/.ssh/id_rsa
source $HOME/.keychain/$HOSTNAME-sh

################################################################################
# ssh english

# echo "  (0) localhost"
# echo -e "  (1) ${host[1]}\t\t(default)"
# echo -n "Destination [0-$top]: "
# echo -n "We haven't conquered that host yet. [0-$top]: " (number greater than top)
# echo -n "That destination is above your pay grade, sir. [0-$top]: " (non-number)
# echo "Automatically starting up tmux"
