# Salto 1
##192.168.0.92
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-int "table=0, priority=100, in_port=br-int-p1, ip, nw_src=10.80.2.1, nw_dst=10.83.1.7, actions=mod_dl_dst=90:00:00:00:00:01, output=int-br-ex" --names
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=ex-br-int, dl_dst=90:00:00:00:00:01, actions=output=p1p1"


##192.168.0.40
docker exec -u 0 openvswitch_vswitchd ovs-vsctl show br-ex
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=em2, dl_dst=90:00:00:00:00:01, actions=output=phy-br-ex"
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=int-br-ex, dl_dst=90:00:00:00:00:01, actions=output=qvo8e75c4ec-c4"

# Salto 2
##192.168.0.40
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=qvo8e75c4ec-c4,  priority=100, dl_dst=90:00:00:00:00:01, actions=mod_dl_dst=90:00:00:00:00:02, output=int-br-ex"
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=phy-br-ex, dl_dst=90:00:00:00:00:02, actions=output=em2"

##192.168.0.92
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "in_port=p1p1, dl_dst=90:00:00:00:00:02, actions=output=p1p2" --names

##192.168.0.41
docker exec -u 0 openvswitch_vswitchd  ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=em2, dl_dst=90:00:00:00:00:02, actions=output=phy-br-ex" --names
docker exec -u 0 openvswitch_vswitchd  ovs-ofctl add-flow br-int "table=0, priority=100, in_port=int-br-ex, dl_dst=90:00:00:00:00:02, actions=output=qvobc09b88d-23" --names

# Salto 3
##192.168.0.41
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=qvobc09b88d-23, dl_dst=90:00:00:00:00:02, actions=mod_dl_dst=90:00:00:00:00:03, output=qvob5d1acfa-e7" --names

# Salto 4
##192.168.0.41
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=qvob5d1acfa-e7, dl_dst=90:00:00:00:00:03, actions=mod_dl_dst=90:00:00:00:00:04, output=int-br-ex" --names

# Salto 4
##192.168.0.41
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=qvob5d1acfa-e7, dl_dst=90:00:00:00:00:03, actions=mod_dl_dst=90:00:00:00:00:04, output=int-br-ex" --names
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=phy-br-ex, dl_dst=90:00:00:00:00:04, actions=output=em2" --names

##192.168.0.92
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "table=0, priority=100,  in_port=p1p2, dl_dst=90:00:00:00:00:04, actions=output=ex-br-sfc" --names
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-sfc "table=0, priority=100, in_port=sfc-br-ex dl_dst=90:00:00:00:00:04, actions=output=tun0" --names

##192.168.0.78
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-sfc "table=0, priority=100, in_port=tun0 dl_dst=90:00:00:00:00:04, actions=output=sfc-br-ex" --names
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=ex-br-sfc, dl_dst=90:00:00:00:00:04, actions=output=p4p1" --names
ip route add 10.81.0.0/16 dev p4p4 via 10.82.255.254
iptables -D INPUT -j REJECT --reject-with icmp-host-prohibited

## 192.168.0.92
ip route add 10.82.0.0/16 dev p1p4 via 10.81.255.254
iptables -D INPUT -j REJECT --reject-with icmp-host-prohibited

## 192.168.0.50
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=em2, dl_dst=90:00:00:00:00:04, actions=output=phy-br-ex"
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=int-br-ex, dl_dst=90:00:00:00:00:04, actions=output=qvoc6d5fefc-a5"

## Salto 5
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "in_port=qvoc6d5fefc-a5, dl_dst=90:00:00:00:00:04, actions=mod_dl_dst=fa:16:3e:f8:21:5d, output=qvoa3fe65dd-51"
# Eu preciso retornar o pacote as condições originais

## Fazer ARP Responder em todos os nós!

# A volta!
## 192.168.0.50
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-int "table=0, priority=100, in_port=qvoa3fe65dd-51, ip, nw_src=10.83.1.7, nw_dst=10.0.0.1, actions=mod_dl_dst=90:00:00:00:00:05, output=int-br-ex" --names
docker exec -u 0 openvswitch_vswitchd ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=phy-br-ex, dl_dst=90:00:00:00:00:05, actions=output=em2"  --names
##192.168.0.78
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=p4p1, dl_dst=90:00:00:00:00:05, actions=output=ex-br-sfc" --names
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-sfc "table=0, priority=100, in_port=sfc-br-ex, dl_dst=90:00:00:00:00:05, actions=output=tun0" --names

##192.168.0.92
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-sfc "table=0, priority=100, in_port=tun0, dl_dst=90:00:00:00:00:05, actions=output=sfc-br-ex" --names
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-ex "table=0, priority=100, in_port=ex-br-sfc, dl_dst=90:00:00:00:00:05, actions=output=ex-br-int" --names
docker exec -u 0 rodolfo-openvswitch ovs-ofctl add-flow br-int "table=0, priority=100, in_port=int-br-ex, dl_dst=90:00:00:00:00:05, actions=mod_dl_dst=06:0e:4e:ab:57:9f, output=br-int-p1" --names
