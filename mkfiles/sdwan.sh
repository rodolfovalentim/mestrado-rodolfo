#!/bin/sh /etc/rc.common

START=10

start() {

    ROUTER_NS="qrouter"
    ROUTER_GW="gwqrouter"
    ROUTER_GW_PEER="gwqrouterpeer"
    ACCESS="eth0.1"
    ACCESS_LOCAL="eth0.2"
    WAN1="eth0.3"
    WAN2="eth0.4"
    LAN="eth0.5"

    ip link set $WAN1 up
    ip link set $WAN2 up
    ip link set $LAN up
    ip link set $ACCESS up

    ovs-ctl start
    ovs-vsctl --may-exist add-br br-lan
    ip addr add 192.168.0.2/24 dev br-lan
    ovs-vsctl --may-exist  add-port br-lan $LAN 

    ovs-vsctl --may-exist add-br br-ex
    ip addr add 192.168.1.2/30 dev br-ex
    ip link set br-ex up
    ovs-vsctl --may-exist add-port br-ex $WAN1
    ovs-vsctl --may-exist add-port br-ex $WAN2

    ip netns add qrouter

    ip netns exec qrouter ip link set dev lo up
    ip link add gwlan type veth peer name gwlanpeer
    ip link add gwqrouter type veth peer name gwqrouterpeer
    ip link set gwlanpeer netns qrouter
    ip link set gwqrouterpeer netns qrouter
    ip link set gwlan up
    ip link set gwqrouter up
    
    ip netns exec qrouter ip addr add 192.168.0.1/24 dev gwlanpeer
    ip netns exec qrouter ip link set gwlanpeer up
    ip netns exec qrouter ip addr add 192.168.1.1/30 dev gwqrouterpeer
    ip netns exec qrouter ip link set gwqrouterpeer up
    ip netns exec qrouter echo nameserver 1.1.1.1 > /etc/resolv.conf

    echo "======= Global Scope Interfaces ======"
    ifconfig $WAN1
    ifconfig $WAN2
    ifconfig $LAN 

    echo "======= OpenvSwitch Bridges ======"
    ovs-vsctl show

    echo "======= qRouter Scope Interfaces ======"
    ip netns exec qrouter ifconfig 

    # cat /etc/dnsmasq.conf
    # dhcp-range=192.168.0.20,192.168.0.254,255.255.255.0 
    # dhcp-option=3,192.168.0.1 
    # dhcp-option=6,1.1.1.1 
    # log-dhcp
    # log-queries
    # log-facility=/tmp/dnsmasq.log

    echo "====== Starting dnsmasq ======"
    dnsmasq

    # Client
    # [Interface]
    # PrivateKey = IM0ZPWsE2n1NjV57bpm7dWdA49/dJ7lknUSt58nJalw= 
    # ListenPort = 51820

    # [Peer]
    # PublicKey = Z6kg2M+hja3TDMoLJbo6sxNF5tDrxxQIvIlqmHRlowU=
    # AllowedIPs = 10.200.200.0/24
    # Endpoint = 200.137.66.110:51820
    # PersistentKeepalive = 25

    # Server
    # [Peer]
    # PublicKey = pMHTXGRIfK/rEr6hHLiBq/bngBbo+BXioTnzMesUuGM=
    # AllowedIPs = 10.200.200.8/32

    echo "======= Starting Wireguard VPN ======"
    ip netns exec qrouter ip link add dev wg0 type wireguard
    ip netns exec qrouter ip address add dev wg0 10.200.200.8/24
    ip netns exec qrouter wg setconf wg0 /etc/wireguard/wg0.conf
    ip netns exec qrouter ip link set wg0 up
    ip netns exec qrouter wg


    echo "======= Setting routing ======"
    ip netns exec qrouter ip route add default via 192.168.1.2 dev gwqrouterpeer
    ip netns exec qrouter sysctl -w net.ipv4.ip_forward=1 

    ovs-vsctl --may-exist add-port br-lan gwlan
    ovs-vsctl --may-exist add-port br-ex gwqrouter

    ip addr add 192.168.0.2/24 dev br-lan
    ip link set br-lan up

    DLSRC=$( cat /sys/class/net/$ROUTER_GW/address )
    DLDST=$( ip netns exec $ROUTER_NS cat /sys/class/net/$ROUTER_GW_PEER/address )
    MACETH1=$( cat /sys/class/net/$WAN1/address )
    MACETH2=$( cat /sys/class/net/$WAN2/address )

    echo "===== ETHERNET INFO ====="
    echo "MAC SRC: $DLSRC"
    echo "MAC DEST: $DLDST"
    echo "MAC WAN1: $MACETH1"
    echo "MAC WAN2: $MACETH2"

    echo "===== Creating Groups ====="
    ovs-ofctl -O OpenFlow15 add-group --may-create br-ex group_id=1,type=select,bucket=bucket_id:1,actions="resubmit(,1)",weight=1,bucket=bucket_id:2,actions="resubmit(,2)",weight=1

    echo "===== Installing WatchDog Flows ====="
    ovs-ofctl -O OpenFlow13 del-flows br-ex
    ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, priority=10, ip, in_port=$ROUTER_GW, actions=group:1" --names
    ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, priority=100, icmp, nw_dst=8.8.8.8, in_port=$ROUTER_GW, actions=resubmit(,1)"  --names
    ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, priority=100, icmp, nw_dst=8.8.4.4, in_port=$ROUTER_GW, actions=resubmit(,2)"  --names
    ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, priority=0,actions=output:NORMAL"  --names

    echo "===== Getting WAN1 info ====="
    OFFERED_IP_WAN1="192.168.15.99"
    HEX_OFFERED_IP_WAN1=`python -c "print ''.join([hex(int(x)+256)[3:] for x in '$OFFERED_IP_WAN1'.split('.')])"`
    ROUTER_IP_WAN1="192.168.15.1"
    SUBNET_WAN1="255.255.255.0"

    if [ "$OFFERED_IP_WAN1" ];
    then 
        # MAC_GW_WAN1=$(arping -I $WAN1 -s 0.0.0.0 -f $ROUTER_IP_WAN1 | grep "reply" | echo $(cut -d' ' -f5) | tail -c +2 | head -c -2)
        MAC_GW_WAN1="c0:3d:d9:03:a1:28"
        echo "=== WAN 1 ==="
        echo "Offered IP: $OFFERED_IP_WAN1"
        echo "Hex Offered IP: $HEX_OFFERED_IP_WAN1"
        echo "Router IP: $ROUTER_IP_WAN1 $MAC_GW_WAN1"
        echo "Subnet Mask: $SUBNET_WAN1"

        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=1, ip,action=ct(commit,zone=1,nat(src=$OFFERED_IP_WAN1)),mod_dl_src=$MACETH1,mod_dl_dst=$MAC_GW_WAN1,output=$WAN1"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=10, priority=100,ct_state=-trk,ip,action=ct(table=10,zone=1,nat)"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=10, priority=100,ct_state=+est,ct_zone=1,ip,action=mod_dl_src=$DLSRC,mod_dl_dst=$DLDST, output=$ROUTER_GW"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, priority=100,in_port=$WAN1,actions=resubmit(,10)"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, arp, in_port=$WAN1, nw_dst=$OFFERED_IP_WAN1 \
                                                actions= \
                                                move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[], \
                                                mod_dl_src=$MACETH1, \
                                                load:0x2->NXM_OF_ARP_OP[], \
                                                move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[], \
                                                move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[], \
                                                load:0x{$MACETH1//:}->NXM_NX_ARP_SHA[], \
                                                load:0x$HEX_OFFERED_IP_WAN1->NXM_OF_ARP_SPA[], in_port"  --names
    else
        echo "=== WAN 1 not UP ==="
    fi

    OFFERED_IP_WAN2="192.168.15.100"
    HEX_OFFERED_IP_WAN2=`python -c "print ''.join([hex(int(x)+256)[3:] for x in '$OFFERED_IP_WAN2'.split('.')])"`
    ROUTER_IP_WAN2="192.168.15.1"
    SUBNET_WAN2="255.255.255.0"

    if [ "$OFFERED_IP_WAN2" ];
    then 
        #MAC_GW_WAN2=$(arping -I $WAN2 -s 0.0.0.0 -f $ROUTER_IP_WAN2 | grep "reply" | echo $(cut -d' ' -f5) | tail -c +2 | head -c -2)
        MAC_GW_WAN2="c0:3d:d9:03:a1:28"
        echo "=== WAN 2 ==="
        echo "Offered IP: $OFFERED_IP_WAN2"
        echo "Hex Offered IP: $HEX_OFFERED_IP_WAN2"
        echo "Router IP: $ROUTER_IP_WAN2 $MAC_GW_WAN2"
        echo "Subnet Mask: $SUBNET_WAN2"

        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=2, ip,action=ct(commit,zone=2,nat(src=$OFFERED_IP_WAN2)),mod_dl_src=$MACETH2, mod_dl_dst=$MAC_GW_WAN2, output=$WAN2"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=20, priority=100,ct_state=-trk,ip,action=ct(table=20,zone=2,nat)"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=20, priority=100,ct_state=+est,ct_zone=2,ip,action=mod_dl_src=$DLSRC,mod_dl_dst=$DLDST, output=$ROUTER_GW"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, priority=100,in_port=$WAN2,actions=resubmit(,20)"  --names
        ovs-ofctl -O OpenFlow13 add-flow br-ex "table=0, arp, in_port=$WAN2, nw_dst=$OFFERED_IP_WAN2 \
                                                actions= \
                                                move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[], \
                                                mod_dl_src=$MACETH2, \
                                                load:0x2->NXM_OF_ARP_OP[], \
                                                move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[], \
                                                move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[], \
                                                load:0x${MACETH2//:}->NXM_NX_ARP_SHA[], \
                                                load:0x$HEX_OFFERED_IP_WAN2->NXM_OF_ARP_SPA[], in_port"  --names

    else
        echo "=== WAN 2 not UP ==="
    fi
}   

