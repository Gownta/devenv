# zsh-specific profile

# Command edit mode
bindkey -v

# History
setopt HIST_IGNORE_DUPS

# Misc

# Prompt
PROMPT=$'%(?..%F{red}%B[Exit %?]\n%b%f)%F{cyan}%~ %F{red}\U2771%F{208}\U2771%F{green}\U2771%f '
RPROMPT='%*'
