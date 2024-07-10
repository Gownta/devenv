# zsh-specific profile

# Command edit mode
bindkey -v

# History
setopt HIST_IGNORE_DUPS

# Misc

# Prompt source control support
# Official docs
#   https://zsh.sourceforge.io/Doc/Release/User-Contributions.html#Version-Control-Information
# Useful docs
#   https://arjanvandergaag.nl/blog/customize-zsh-prompt-with-vcs-info.html
#autoload -Uz vcs_info
#precmd () { vcs_info }
#zstyle ':vcs_info:*' enable git hg  # each scm has overhead
#zstyle ':vcs_info:*' formats "%r/ $(qqq %S) %b %m %u %c"
# Use ${vcs_info_msg_0_} in PROMPT

# Prompt specification
setopt PROMPT_SUBST
PROMPT=$'%(?..%F{red}%B[Exit %?]\n%b%f)${PROMPT_VAR_HOST}%F{cyan}$(prompt_dir_sub)%f $PROMPT_VAR_ART '
RPROMPT='%*'
