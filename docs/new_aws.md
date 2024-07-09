# AWS hosts

Access:
`ssh ec2-user@EC2-HOST`
Note: `-i ~/.ssh/id_ed25519` is not necessary; that's one of the default identity files

Install zsh:
```
sudo yum install zsh -y
```

Give wheel users super permissions
(note: can change after the fact using `sudo usermod`)
```
sudo visudo
  # near the bottom, uncomment this line:
  # %wheel ALL=(ALL) NOPASSWD: ALL
  # ctrl-x to exit
```

Create user njormrod with ssh permission:
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/managing-users.html
/etc/passwd
```
sudo adduser --shell /usr/bin/zsh --comment Me --groups wheel njormrod
cat .ssh/authorized_keys
sudo su - njormrod
cd /home/njormrod
mkdir .ssh
chmod 700 .ssh
touch .ssh/authorized_keys
chmod 600 .ssh/authorized_keys
# add the content from cat, above
```

Now I can ssh in with njormrod@
...and since I am already njormrod, I can just drop that part

On aws server:
```
ssh-keygen -t ed25519 -C "nicholas.ormrod@gmail.com"
```
On github, settings > SSH and GPG keys, click the New SSH Key button, add the .pub file

Install git, get my dotfiles
```
sudo yum install git -y
git clone git@github.com:Gownta/devenv.git
```

