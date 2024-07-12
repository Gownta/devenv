# Systemd

Add my own systemd files to ~/.config/systemd/user/
Use `njormrod$ systemctl --user ...` instead of `root$ systemctl ...`




My systemd files should live in /etc/systemd/system
Rather, there should be symlinks from there to devenv/systemd

## Starting and observing

```
systemctl start FILE
systemctl status FILE
journalctl -S today -u FILE
```

`systemctl enable` enables a service to be started on boot

If I make changes to a systemd file, then `systemctl daemon-reload`

## All files

https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#

```
[Unit]
Description=...
Wants=FILE1 FILE2 ...
Requires=FILE1 FILE2 ...

[Install]
WantedBy=multi-user.target
```

Install is required to enable the service. In the case of multi-user.target, when that stage is reached then this unit will be enabled.

## .service files

https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html

```
[Service]
ExecStart=the-command-to-execute
```

## .timer files

https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html#

```
[Timer]
OnBootSec=<time after boot to start>
OnCalendar=<time spec>
Unit=what to run  # defaults to <timer-filename>.service
```

Time triggers intentionally jitter by +[0,1) minutes

## Time specification

https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html#

Examples:
```
Thu,Fri 2012-*-1,5 11:12:13

The above refers to 11:12:13 of the first or fifth day of any month of the year 2012, but only if that day is a Thursday or Friday.


*-*-* *:*:00

^ minutely
```


# References

https://www.freedesktop.org/software/systemd/man/latest
https://docs.fedoraproject.org/en-US/quick-docs/systemd-understanding-and-administering/
https://opensource.com/article/20/7/systemd-timers
https://unix.stackexchange.com/questions/224992/where-do-i-put-my-systemd-unit-file
https://wiki.archlinux.org/title/Systemd/User
