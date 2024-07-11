# Jupyter

AWS Jupyter docs: https://docs.aws.amazon.com/dlami/latest/devguide/setup-jupyter.html

```
pip3 install jupyter
jupyter notebook --generate-config
jupyter notebook password

mkcd ~/.ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mykey.key -out mycert.pem

# in the config file, add the following lines:
import os
c.ServerApp.certfile = os.path.expanduser('~/.ssl/mycert.pem')
c.ServerApp.keyfile = os.path.expanduser('~/.ssl/mykey.key')
c.ServerApp.root_dir = os.path.expanduser('~/jupyter')

# start a notebook server
jupyter notebook
```

on mbp:
```
ssh -NfL 8888:localhost:8888 <Public DNS of EC2 Host>
```

https://localhost:8888
Advanced > visit anyways
