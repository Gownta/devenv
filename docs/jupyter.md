# Jupyter

AWS Jupyter docs: https://docs.aws.amazon.com/dlami/latest/devguide/setup-jupyter.html

```
pip3 install jupyter
jupyter notebook password

mkcd ~/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mykey.key -out mycert.pem

jupyter notebook --certfile=~/ssl/mycert.pem --keyfile ~/ssl/mykey.key
```

on mbp:
```
ssh -NfL 8888:localhost:8888 <Public DNS of EC2 Host>
```

https://localhost:8888
Advanced > visit anyways
