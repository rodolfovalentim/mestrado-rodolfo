# 192.168.0.50
docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 \
    tcp:192.168.0.50:6634 tcp:192.168.0.50:6636

docker exec -u 0 -it openvswitch_vswitchd ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 \
    tcp:192.168.0.50:6634 tcp:192.168.0.50:6635

docker run -t -d --name=ryu -p 6634:6634 -p 8087:8087 rodolfo/ubuntu-source-ryu ryu-manager ryu.app.rest_topology --observe-links --ofp-tcp-listen-port 6634 --wsapi-host 0.0.0.0 --wsapi-port 8087
