# Systemd

Add my own systemd files to ~/.config/systemd/user/ (rather, symlink that dir to my systemd dir)
Use `njormrod$ systemctl --user ...` instead of `root$ systemctl ...`


# Observing

```
systemctl --user {status,enable} idle_shutdown.{timer,service}
journalctl --user -S today -u idle_shutdown.service
```

If I make changes to a systemd file, then `systemctl --user daemon-reload`


# Format

https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html
https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html

.*
```
[Unit]
Description=mandatory description of this file
Wants=
Requires=

[Install]
WantedBy=default.target  # this is automatically executed for user systemd
```

.service
```
[Service]
ExecStart=the-command-to-execute
```

.timer
```
[Timer]
OnBootSec=<time after boot to start>
OnCalendar=<time spec>
Unit=what to run  # defaults to <timer-filename>.service
```

Note: Time triggers intentionally jitter by +[0,1) minutes


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
