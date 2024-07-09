# AWS hosts

Access:
`ssh -i id_25519 ec2-user@EC2-HOST`

Install zsh:
```
sudo yum install zsh -y
```

Create user njormrod with ssh permission:
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/managing-users.html
```
sudo adduser --shell /usr/bin/zsh njormrod
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

Setup zsh:
```
sudo yum install util-linux-user -y
sudo chsh -e $(which zsh) $USER
```

...or change the default shell manually
```
sudo vim /etc/passwd
```
