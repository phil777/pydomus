# PyDomus

Python interface ot LifeDomus SOAP API.

This is a very early stage. Very few features are implemented and some
things are even hard coded.

## PyDomus

PyDomus can use the SOAP interface on port 8080 or 8443. Base URL and password can be
provided on command line or in environment variables.

```
export PYDOMUS_BASE_URL=https://192.168.1.20:8443/
export PYDOMUS_PASSWORD=foobar
```

Example of commands
```
pydomus  show connectors
pydomus  show rooms
pydomus  show domains
pydomus  add knx-light "My kitchen lamp" Kitchen 6/0/4 6/1/4
pydomus  add knx-dimmer "My basement dimmer" Basement 6/0/7 6/1/7 6/3/7 6/4/7
```



## How LifeDomus CS works

The SOAP interface runs on ports 8080 and 8443 of the LifeDomus box.


When LifeDomus CS starts it asks for two ports: 8443 and 51023.
It then retrieves a ssh private key in putty format here:
https://192.168.1.20:8443/SecureConnect?format=ppk

By the way, you can convert it to openssh using `putty-tools` package.

```
puttygen /tmp/ld.ppk -O public-openssh -o id_lifedomus.pub
puttygen /tmp/ld.ppk -O private-openssh -o id_lifedomus
```

Then it creates a ssh tunnel to reach ports 8080 and 8090.
```
plink -L 52862:ld-remote:8080 -L 54863:ld-remote:8090 -ssh ld-remote@<lifedomus IP> -P 51023 -N -i <ppkfile>
```

It is strange since it could directly connect to 8443 to have a secure communication.

Port 8090 seems to deliver variable updates (temperature, etc.).

Then it manipulates data through the SOAP interface.


