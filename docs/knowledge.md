# Knowledge

## System Users

I am njormrod. That is a system user, configured per machine.

Source of truth: /etc/passwd

Some commands:
```
sudo adduser --shell /usr/bin/zsh --comment Me --groups wheel njormrod
man usermod
sudo userdel -r <unixname>
```

AWS docs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/managing-users.html
