# 192.168.0.50
docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 \
    tcp:192.168.0.50:6634 tcp:192.168.0.50:6636

docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 \
    tcp:192.168.0.50:6634 tcp:192.168.0.50:6635