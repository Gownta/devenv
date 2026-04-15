# Italics

I want iterm and tmux to support italics text.

The TERM variable states what font formats the terminal supports.
When ssh'ing, the server knows the client's TERM, and only sends markup that the client understands.

Initially, my devserver tmux was set to screen-256color.
screen-256color is the lowest common denominator. It doesn't support italics.
My mac had xterm-256color, which *does* support italics.
When I changed my devserver to xterm-256color, it still didn't support italics...
...because my devserver's xterm-256color is outdated. They agreed to use xterm-256color, but were mismatched.
I determined that my devserver's tmux-256color DOES support italics.
...however, my mac was telling tmux "I use xterm-256color", which my devserver thought did not support italics, and so the devserver was dropping all the italics markup.
So I changed my ssh script to set TERM=tmux-256color (which my mac also supports)
And now, finally, I have italics on my devserver.
