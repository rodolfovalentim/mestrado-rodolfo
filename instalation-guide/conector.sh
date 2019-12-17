# 192.168.0.78

curl -sSL https://get.docker.io | bash
usermod -aG wheel stack
systemctl enable docker
systemctl start docker
systemctl status docker

# 192.168.0.92
PROVIDER_INT=em2
NUVEM1_INT=p1p1
NUVEM2_INT=p1p2
INTERNAL_INT=p1p4
REMOTE_IP=10.82.0.1

# 192.168.0.78
PROVIDER_INT=em2
NUVEM1_INT=p4p1
NUVEM2_INT=p4p2
INTERNAL_INT=p4p4
REMOTE_IP=10.81.0.1

# Copy the file Dockerfile-ovs
docker build . -t rodolfo/centos-source-openvswitch
docker run -t -d --net=host --name=rodolfo-openvswitch -v /lib:/lib --privileged rodolfo/centos-source-openvswitch /bin/bash
docker exec -u 0 rodolfo-openvswitch ovs-ctl start

# br-int vai estar conectada a rede provider
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-br br-int
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-int $PROVIDER_INT

# Conectando as interfaces das outras nuvens a br-ex
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-br br-ex
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-ex $NUVEM1_INT 
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-ex $NUVEM2_INT 

docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-br br-sfc
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=vxlan options:remote_ip=$REMOTE_IP options:key=123

# Conexão entre a br-int e br-ex
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-int int-br-ex
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface int-br-ex type=patch
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface int-br-ex options=peer=ex-br-int

# Conexão entre a br-ex e br-int
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-ex ex-br-int
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface ex-br-int type=patch
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface ex-br-int options=peer=int-br-ex

# Conexão entre a br-sfc e a br-ex
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-sfc sfc-br-ex
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface sfc-br-ex type=patch
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface sfc-br-ex options=peer=ex-br-sfc

# Conexão entre a br-ex e a br-sfc
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-ex ex-br-sfc
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface ex-br-sfc type=patch
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set interface ex-br-sfc options=peer=sfc-br-ex


docker exec -u 0 rodolfo-openvswitch ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 tcp:192.168.0.50:6634
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 tcp:192.168.0.50:6634
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set-controller br-sfc tcp:127.0.0.1:6633 tcp:192.168.0.50:6634

docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-int "table=0, priority=0 actions=NORMAL"
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "table=0, priority=0 actions=NORMAL"


# 192.168.0.92 nerds-09
sudo ip netns add src
sudo ip link add name veth1 type veth peer name br-int-p1
sudo ip link set dev veth1 netns src
sudo ip netns exec src ifconfig veth1 10.0.0.1/24 up
sudo ip netns exec src arp -s 10.0.0.8 90:00:00:00:00:01
ifconfig br-int-p1 up


docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-int br-int-p1
docker exec -u 0 rodolfo-openvswitch ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 \
    tcp:192.168.0.40:6634 