# Additional Setup

...sigh, some things are hard to install

- eza
  - cargo does a good job, except man page
  - generate the man page by:
    1. Going to the github page to get the man pages in markdown
    2. Updating "$version" with the version, as found in Cargo.toml
    3. Converting from markdown to man on https://pandoc.org/try/
    4. All lines that start with . need a newline between them and the line before
    5. gzip the file (`gz <filename>`)
    6. sudo cp the file to /usr/local/share/man/man1
    7. `sudo mandb`
    8. `man eza`
- haskell
  - https://www.haskell.org/ghcup/install/
  - add ~/.ghcup/bin to PATH
  - don't worry about package "realpath"
- pandoc
  - https://pandoc.org/installing.html
  - git clone https://github.com/jgm/pandoc
  - cabal install pandoc-cli
  - ...sigh, I cannot get it to work on ec2
