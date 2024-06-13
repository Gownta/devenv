# zsh-specific profile

# Command edit mode
bindkey -v

# History
setopt HIST_IGNORE_DUPS

# Misc

# Prompt
setopt PROMPT_SUBST
PROMPT=$'%(?..%F{red}%B[Exit %?]\n%b%f)%F{cyan}$(prompt_dir_sub) %F{red}\U2771%F{208}\U2771%F{green}\U2771%f '
RPROMPT='%*'
