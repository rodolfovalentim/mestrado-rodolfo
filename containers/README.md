# docker build . -t rodolfo/centos-source-openvswitch

# docker run -it --net=host --name=rodolfo-openvswitch -v /lib:/lib --privileged rodolfo/centos-source-openvswitch /bin/bash

# docker build . -t rodolfo/ubuntu-source-ryu

# docker run -itd --name=ryu -p 6653:6653 -p 8080:8080 rodolfo/ubuntu-source-ryu ryu-manager ryu.app.ofctl_rest ryu.app.simple_switch
