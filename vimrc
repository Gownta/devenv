set tabstop=2
set ruler
set nolist
set showcmd
set showmode
set showmatch
set scrolljump=5
set sidescroll=10
set noerrorbells
set backspace=indent,eol,start
set tags=tags;/
set undolevels=1000
set viminfo='50,"50
set modelines=0
set expandtab
set shiftwidth=2
set softtabstop=2
set incsearch
set scrolloff=1
set autoindent
set number
set numberwidth=5
set mouse=a
set display=lastline
set hlsearch

:highlight ExtraWhitespace ctermbg=red guibg=red
:au InsertEnter * match ExtraWhitespace /\s\+\%#\@<!$/
:au InsertLeave * match ExtraWhitespace /\s\+$/

:map Q <Nop>

syntax on
