ryu-manager ryu.app.rest_topology --observe-links --ofp-tcp-listen-port 6634 --wsapi-host 0.0.0.0 --wsapi-port 8080

ryu-manager core-controller.py --ofp-tcp-listen-port 6635 --wsapi-host 0.0.0.0 --wsapi-port 8081

ryu-manager edge-controller.py ryu.app.ofctl_rest --ofp-tcp-listen-port 6636 --wsapi-host 0.0.0.0 --wsapi-port 8082

ryu-manager external-controller.py ryu.app.ofctl_rest --ofp-tcp-listen-port 6637 --wsapi-host 0.0.0.0 --wsapi-port 8083