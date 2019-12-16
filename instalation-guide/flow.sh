# Salto 1
##192.168.0.92
ovs-ofctl add-flow br-int "in_port=qvoxxxx, ip, nw_src=10.0.0.1, nw_dst=10.0.0.2, \
    tp_src=8012, tp_dst=8013, actions=dl_src=90:00:00:00:00:01, output=2"

ovs-ofctl add-flow br-ex "in_port=int-br-ex, dl_src=90:00:00:00:00:01, actions=output=2"

##192.168.0.40
ovs-ofctl add-flow br-ex "dl_src=90:00:00:00:00:01, actions=output=2"
ovs-ofctl add-flow br-int "in_port=br-ex, dl_src=90:00:00:00:00:01, actions=output=1"

# Salto 2
##192.168.0.40
ovs-ofctl add-flow br-int "in_port=vm1, dl_src=90:00:00:00:00:01, \
    actions=dl_src=90:00:00:00:00:02, output=int-br-ex"

##192.168.0.92
ovs-ofctl add-flow br-ex "in_port=ex-br-int, dl_src=90:00:00:00:00:02, actions=output=em2"

##192.168.0.41
ovs-ofctl add-flow br-ex "dl_src=90:00:00:00:00:02, actions=output=2"
ovs-ofctl add-flow br-int "in_port=br-ex, dl_src=90:00:00:00:00:02, actions=output=1"

# Salto 3
##192.168.0.41
ovs-ofctl add-flow br-int "in_port=vm2, dl_src=90:00:00:00:00:02, \
    actions=dl_src=90:00:00:00:00:03, output=vm3"

# Salto 4
##192.168.0.41
ovs-ofctl add-flow br-int "in_port=vm3, dl_src=90:00:00:00:00:03, \
    actions=dl_src=90:00:00:00:00:04, output=int-br-ex"

ovs-ofctl add-flow br-ex "dl_src=90:00:00:00:00:04, actions=output=em2"

##192.168.0.92
ovs-ofctl add-flow br-ex "dl_src=90:00:00:00:00:04, actions=output=ex-br-sfc"
ovs-ofctl add-flow br-sfc "dl_src=90:00:00:00:00:04, actions=output=tun0"


##192.168.0.78
ovs-ofctl add-flow br-sfc "dl_src=90:00:00:00:00:04, actions=output=sfc-br-ex"
ovs-ofctl add-flow br-ex "dl_src=90:00:00:00:00:04, actions=output=3"

##192.168.0.50
ovs-ofctl add-flow br-int "in_port=int-br-ex, dl_src=90:00:00:00:00:04, \
    actions=output=vm4"

# Salto 5
ovs-ofctl add-flow br-int "in_port=vm4, dl_src=90:00:00:00:00:04, \
    actions=output=vm4"

# Fazer ARP Responder em todos os nós!