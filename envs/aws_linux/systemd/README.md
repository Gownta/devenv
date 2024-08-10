# User systemd

Make symlink ~/.config/systemd/user -> this directory

The default.target.wants can be remade like `systemctl --user enable idle_shutdown.timer` (in ~/.config/systemd/user/).

See active controllers like `systemctl --user list-units --state=active`
