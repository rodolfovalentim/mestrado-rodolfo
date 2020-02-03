# docker build . -t rodolfo/centos-source-openvswitch

# docker run -t -d --net=host --name=rodolfo-openvswitch -v /lib:/lib --privileged rodolfo/centos-source-openvswitch /bin/bash

# docker exec -u 0 rodolfo-openvswitch ovs-ctl start

# docker build . -t rodolfo/ubuntu-source-ryu

# docker run -t -d --name=ryu -p 6634:6634 -p 8087:8087 rodolfo/ubuntu-source-ryu ryu-manager ryu.app.rest_topology --observe-links --ofp-tcp-listen-port 6634 --wsapi-host 0.0.0.0 --wsapi-port 8087

# need to edit the file  and add the following -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock 

https://docs.docker.com/engine/reference/commandline/dockerd/
vi /etc/systemd/system/docker.service.d/kolla.conf