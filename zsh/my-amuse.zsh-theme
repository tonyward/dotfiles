# vim:ft=zsh ts=2 sw=2 sts=2

# Must use Powerline font, for \uE0A0 to render.
ZSH_THEME_GIT_PROMPT_PREFIX=" on %{$fg[magenta]%}\uE0A0 "
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[red]%}!"
ZSH_THEME_GIT_PROMPT_UNTRACKED="%{$fg[green]%}?"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_RUBY_PROMPT_PREFIX="%{$fg_bold[red]%}‹"
ZSH_THEME_RUBY_PROMPT_SUFFIX="›%{$reset_color%}"

PROMPT='
%{$fg_bold[blue]%}%~%{$reset_color%}$(git_prompt_info) ⌚ %{$fg_bold[magenta]%}%*%{$reset_color%}
(: '

#RPROMPT='$(ruby_prompt_info)'
if [ $(id -u) -eq 0 ];
then # you are root, make the Rprompt magenta
    RPROMPT='$(virtualenv_prompt_info)%{$fg_bold[magenta]%}%n%{$reset_color%}@%{$fg_bold[magenta]%}%m%{$reset_color%}%'
else
    RPROMPT='$(virtualenv_prompt_info)%{$fg_bold[blue]%}%n%{$reset_color%}@%{$fg_bold[blue]%}%m%{$reset_color%}%'
fi


