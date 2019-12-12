ryu-manager ryu.app.rest_topology --observe-links --ofp-tcp-listen-port 6634 --wsapi-host 0.0.0.0 --wsapi-port 8080

ryu-manager core-controller.py --ofp-tcp-listen-port 6635 --wsapi-host 0.0.0.0 --wsapi-port 8081

ryu-manager edge-controller.py ryu.app.ofctl_rest --ofp-tcp-listen-port 6636 --wsapi-host 0.0.0.0 --wsapi-port 8082

ryu-manager external-controller.py ryu.app.ofctl_rest --ofp-tcp-listen-port 6637 --wsapi-host 0.0.0.0 --wsapi-port 8083

# 192.168.0.40
ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 tcp:192.168.0.40:6634 tcp:192.168.0.40:6636
ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 tcp:192.168.0.40:6634 tcp:192.168.0.40:6635

# 192.168.0.41
ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 tcp:192.168.0.40:6634 tcp:192.168.0.40:6636
ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 tcp:192.168.0.40:6634 tcp:192.168.0.40:6635

# 192.168.0.50
ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 tcp:192.168.0.50:6634 tcp:192.168.0.40:6636
ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 tcp:192.168.0.50:6634 tcp:192.168.0.40:6635

# 192.168.0.78
ovs-vsctl set-controller br-sfc-1 tcp:127.0.0.1:6633 tcp:192.168.0.40:6634
ovs-vsctl set-controller br-sfc-2 tcp:127.0.0.1:6633 tcp:192.168.0.50:6634

# 192.168.0.92
ovs-vsctl set-controller br-int tcp:127.0.0.1:6633 tcp:192.168.0.40:6634 tcp:192.168.0.40:6637
ovs-vsctl set-controller br-ex tcp:127.0.0.1:6633 tcp:192.168.0.40:6634 tcp:192.168.0.40:6635



ryu-manager ryu.app.rest_topology --observe-links --ofp-tcp-listen-port 6634 --wsapi-host 0.0.0.0 --wsapi-port 8080

ryu-manager core-controller.py --ofp-tcp-listen-port 6635 --wsapi-host 0.0.0.0 --wsapi-port 8081

ryu-manager edge-controller.py ryu.app.ofctl_rest --ofp-tcp-listen-port 6636 --wsapi-host 0.0.0.0 --wsapi-port 8082

ryu-manager external-controller.py ryu.app.ofctl_rest --ofp-tcp-listen-port 6637 --wsapi-host 0.0.0.0 --wsapi-port 8083