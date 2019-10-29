# Documentação do SFC Gateway

Após instalado o OVS nas máquinas virtuais, a configuração da VXLAN foi feita seguindo este [tutorial](https://costiser.ro/2016/07/07/overlay-tunneling-with-openvswitch-gre-vxlan-geneve-greoipsec/).

## Configuração de VxLAN usando namespaces

### SFC-GW-1

```bash
sudo ip netns add left
sudo ip link add name veth1 type veth peer name sw1-p1
sudo ip link set dev veth1 netns left
sudo ip netns exec left ifconfig veth1 10.0.0.1/24 up

sudo ovs-vsctl add-br sw1
sudo ovs-vsctl add-port sw1 sw1-p1
sudo ip link set sw1-p1 up
sudo ip link set sw1 up
```

### SFC-GW-2

```bash
sudo ip netns add right
sudo ip link add name veth1 type veth peer name sw2-p1
sudo ip link set dev veth1 netns right
sudo ip netns exec right ifconfig veth1 10.0.0.2/24 up

sudo ovs-vsctl add-br sw2
sudo ovs-vsctl add-port sw2 sw2-p1
sudo ip link set sw2-p1 up
sudo ip link set sw2 up
```

## Usando VxLAN

### SFC-GW-1

```bash
sudo ovs-vsctl del-port sw1 tun0
sudo ovs-vsctl add-port sw1 tun0 -- set interface tun0 type=vxlan options:remote_ip=172.16.30.84 options:key=123
```

### SFC-GW-2

```bash
sudo ovs-vsctl del-port sw2 tun0
sudo ovs-vsctl add-port sw2 tun0 -- set interface tun0 type=vxlan options:remote_ip=172.16.30.86 options:key=123
```

## Usando GREoIPsec

### on vagrant box-1

```bash
sudo ovs-vsctl del-port sw1 tun0
sudo ovs-vsctl add-port sw1 tun0 -- set interface tun0 type=gre options:remote_ip=172.16.30.84 options:psk=test123
```

### on vagrant box-2

```bash
sudo ovs-vsctl del-port sw2 tun0
sudo ovs-vsctl add-port sw2 tun0 -- set interface tun0 type=gre options:remote_ip=172.16.30.86 options:psk=test123
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
sudo ovs-ofctl del-flows sw1
sudo ovs-ofctl add-flow sw1 "ip, in_port=1, actions=output=5"
sudo ovs-ofctl add-flow sw1 "ip, in_port=5, actions=output=1"
sudo ovs-ofctl add-flow sw1 "arp, in_port=1, actions=output=5"
sudo ovs-ofctl add-flow sw1 "arp, in_port=5, actions=output=1"
sudo ovs-ofctl add-flow sw1 "actions=output=NORMAL"
```

## Para instalar os pacotes necessarios ao IPSec

[Link da documentação](http://docs.openvswitch.org/en/latest/tutorials/ipsec/)

```bash
apt-get install dkms strongswan
dpkg -i libopenvswitch*\*.deb openvswitch-common*_.deb \
 openvswitch-switch\__.deb openvswitch-datapath-dkms*\*.deb \
 python-openvswitch*_.deb openvswitch-pki\__.deb \
 openvswitch-ipsec\_\*.deb
```
