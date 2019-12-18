# Documentação do SFC Gateway

Após instalado o OVS nas máquinas virtuais, a configuração da VXLAN foi feita seguindo este [tutorial](https://costiser.ro/2016/07/07/overlay-tunneling-with-openvswitch-gre-vxlan-geneve-greoipsec/).

O cara que salvou o artigo: https://costiser.ro/2016/07/11/performance-review-of-overlay-tunnels-with-openvswitch/

## Configuração de VxLAN usando namespaces

### SFC-GW-1

```bash
sudo ip netns add left
sudo ip link add name veth1 type veth peer name br-sfc-p1
sudo ip link set dev veth1 netns left
sudo ip netns exec left ifconfig veth1 10.0.0.1/24 up

sudo ovs-vsctl add-br br-sfc
sudo ovs-vsctl add-port br-sfc br-sfc-p1
sudo ip link set br-sfc-p1 up
sudo ip link set br-sfc up
```

Ou, em caso de rodando em docker, use como a seguir

```bash
docker exec -u 0 rodolfo-openvswitch  ip netns add left
docker exec -u 0 rodolfo-openvswitch  ip link add name veth1 type veth peer name br-sfc-p1
docker exec -u 0 rodolfo-openvswitch  ip link set dev veth1 netns left
docker exec -u 0 rodolfo-openvswitch  ip netns exec left ifconfig veth1 10.0.0.1/24 up

docker exec -u 0 rodolfo-openvswitch  ovs-vsctl add-br br-sfc
docker exec -u 0 rodolfo-openvswitch  ovs-vsctl add-port br-sfc br-sfc-p1
docker exec -u 0 rodolfo-openvswitch  ip link set br-sfc-p1 up
docker exec -u 0 rodolfo-openvswitch  ip link set br-sfc up
```


### SFC-GW-2

```bash
sudo ip netns add right
sudo ip link add name veth1 type veth peer name br-sfc-p1
sudo ip link set dev veth1 netns right
sudo ip netns exec right ifconfig veth1 10.0.0.2/24 up

sudo ovs-vsctl add-br br-sfc
sudo ovs-vsctl add-port br-sfc br-sfc-p1
sudo ip link set br-sfc-p1 up
sudo ip link set br-sfc up
```

```bash
docker exec -u 0 rodolfo-openvswitch ip netns add right
docker exec -u 0 rodolfo-openvswitch ip link add name veth1 type veth peer name br-sfc-p1
docker exec -u 0 rodolfo-openvswitch ip link set dev veth1 netns right
docker exec -u 0 rodolfo-openvswitch ip netns exec right ifconfig veth1 10.0.0.2/24 up

docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-br br-sfc
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-sfc br-sfc-p1
docker exec -u 0 rodolfo-openvswitch ip link set br-sfc-p1 up
docker exec -u 0 rodolfo-openvswitch ip link set br-sfc up
```

## Usando VxLAN

### SFC-GW-1

```bash
sudo ovs-vsctl del-port br-sfc tun0
sudo ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=vxlan options:remote_ip=172.16.30.84 options:key=123
```

```bash
docker exec -u 0 rodolfo-openvswitch  ovs-vsctl del-port br-sfc tun0
docker exec -u 0 rodolfo-openvswitch  ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=vxlan options:remote_ip=172.16.30.84 options:key=123
```


### SFC-GW-2

```bash
sudo ovs-vsctl del-port br-sfc tun0
sudo ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=vxlan options:remote_ip=172.16.30.86 options:key=123
```

```bash
docker exec -u 0 rodolfo-openvswitch ovs-vsctl del-port br-sfc tun0
docker exec -u 0 rodolfo-openvswitch ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=vxlan options:remote_ip=172.16.30.86 options:key=123
```


## Usando GREoIPsec

### on vagrant box-1

```bash
sudo ovs-vsctl del-port br-sfc tun0
sudo ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=gre options:remote_ip=172.16.30.84 options:psk=test123
```

### on vagrant box-2

```bash
sudo ovs-vsctl del-port br-sfc tun0
sudo ovs-vsctl add-port br-sfc tun0 -- set interface tun0 type=gre options:remote_ip=172.16.30.86 options:psk=test123
```

```bash
ovs-appctl dpif/show
```

### Tentativa de fazer output para porta e o encapsulamento ser automático

Regra que estava instalada:

```bash
cookie=0x0, duration=1511.002s, table=0, n_packets=74, n_bytes=6548, priority=0 actions=NORMAL
```

Regras a serem instaladas no "left":

```bash
sudo ovs-ofctl del-flows br-sfc
sudo ovs-ofctl add-flow br-sfc "ip, in_port=1, actions=output=5"
sudo ovs-ofctl add-flow br-sfc "ip, in_port=5, actions=output=1"
sudo ovs-ofctl add-flow br-sfc "arp, in_port=1, actions=output=5"
sudo ovs-ofctl add-flow br-sfc "arp, in_port=5, actions=output=1"
sudo ovs-ofctl add-flow br-sfc "actions=output=NORMAL"
```

## Para instalar os pacotes necessarios ao IPSec

[Link da documentação](http://docs.openvswitch.org/en/latest/tutorials/ipsec/)

```bash
apt-get install dkms strongswan
dpkg -i libopenvswitch*.deb openvswitch-common*_.deb \
 openvswitch-switch\__.deb openvswitch-datapath-dkms*\*.deb \
 python-openvswitch*_.deb openvswitch-pki\__.deb \
 openvswitch-ipsec\_\*.deb
```
