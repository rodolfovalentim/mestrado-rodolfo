# 192.168.0.40
docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 \
    tcp:192.168.0.40:6634 tcp:192.168.0.40:6636

docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 \
    tcp:192.168.0.40:6634 tcp:192.168.0.40:6635

# 192.168.0.41
docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 \
    tcp:192.168.0.40:6634 tcp:192.168.0.40:6636

docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 \
    tcp:192.168.0.40:6634 tcp:192.168.0.40:6635
