" vimrc

" clang format on save
if 0
  if empty(glob('~/.vim/autoload/plug.vim'))
    silent !curl -fLo ~/.vim/autoload/plug.vim --create-dirs
          \ https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
  endif

  call plug#begin('~/.vim/plugged')
  "Plug 'ctrlpvim/ctrlp.vim'
  Plug 'chiel92/vim-autoformat'
  "Plug 'mileszs/ack.vim'
  call plug#end()

  augroup autofmt
    autocmd! FileType c,cpp autocmd BufWrite <buffer> :Autoformat
  augroup END
endif


set autoindent
set backspace=indent,eol,start
set display=lastline
set expandtab
set hlsearch
set incsearch
set modelines=0
set mouse=a
set noerrorbells
set nolist
set number
set numberwidth=5
set ruler
set scrolljump=1
set scrolloff=1
set shiftwidth=2
set showcmd
set showmatch
set showmode
set sidescroll=10
set smartcase
set softtabstop=2
set tabstop=8
set tags=tags;/
set undolevels=1000
set viminfo='50,"50

:highlight ExtraWhitespace ctermbg=red guibg=red
:au InsertEnter * match ExtraWhitespace /\s\+\%#\@<!$/
:au InsertLeave * match ExtraWhitespace /\s\+$/

:map Q <Nop>

syntax on
colorscheme desert
