curl -sSL https://get.docker.io | bash
usermod -aG wheel stack
systemctl enable docker
systemctl start docker
systemctl status docker

Copy the file Dockerfile-ovs
docker build . -t rodolfo/centos-source-openvswitch
docker run -t -d --net=host --name=rodolfo-openvswitch -v /lib:/lib --privileged rodolfo/centos-source-openvswitch /bin/bash
docker exec -u 0 rodolfo-openvswitch ovs-ctl start
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-br br-sfc1
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-br br-sfc2
