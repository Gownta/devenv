# zsh-specific profile

# Command edit mode
bindkey -v

# History
setopt HIST_IGNORE_DUPS

# History search
# In iTerm, bind cmd-R to send key 0x12 (ctrl-r)
bindkey '^R' history-incremental-search-backward

# Completions
autoload -U compinit
compinit

# Cursor: use a bar instead of a box
# echo -ne '\e[5 q'

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
timer_start=0
njo_time_start() {
  timer_start="$(date +%s%N)"
}
njo_pre_prompt() {
  ~/dev/devenv/bin/prompt_gen.py $timer_start $COLUMNS $?
  timer_start=0
}
preexec_functions+=(njo_time_start)
precmd_functions+=(njo_pre_prompt)
PROMPT=$'%F{238}╰─%f$PROMPT_VAR_ART '
RPROMPT=$'%F{238}─╯%f'
