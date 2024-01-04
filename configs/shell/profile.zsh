# zsh-specific profile

# Command edit mode
bindkey -v

# History
setopt HIST_IGNORE_DUPS

# Misc

# Prompt
PROMPT=$'%(?..%F{red}%B[Exit %?]\n%b%f)%F{cyan}%~ $%f '
RPROMPT='%*'
