from functools import reduce
import json


class Port(object):
    def __init__(self, *args, **kwargs):
        self.dpid = kwargs.get('dpid', None)
        self.port_no = kwargs.get('port_no', None)
        if self.port_no is not None:
            self.port_no = int(self.port_no, 16)

        self.hw_addr = kwargs.get('hw_addr', None)
        self.name = kwargs.get('name', None)

    def __repr__(self):
        return 'Port {}'.format(self.name)


class Link(object):
    def __init__(self, *args, **kwargs):
        self.port_src = Port(**kwargs.get('src'))
        self.port_dst = Port(**kwargs.get('dst'))

    def __repr__(self):
        return 'Link src: {} -> dst: {}'.format(self.port_src, self.port_dst)


class Switch(object):
    def __init__(self, *args, **kwargs):
        self.dpid = kwargs.get('dpid', None)
        self.key = kwargs.get('key', None)
        self.ports = None
        ports = kwargs.get('ports', None)
        if ports is not None:
            self.ports = [Port(**port) for port in ports]

    def __repr__(self):
        return 'Switch {}'.format(self.__dict__)

    def get_dpid(self):
        return self.dpid

    def set_dpid(self, dpid):
        self.dpid = dpid

    def add_port(self, port):
        self.ports.append(port)

    def set_ports(self, ports):
        self.ports = [Port(**port) for port in ports]

    def has_port(self, name):
        for port in self.ports:
            if port.name == name:
                return True
        return False

    def get_core_to_edge_port(self):
        def f(x, switch): return switch.name == 'int-br-ex' and switch or x
        port = reduce(f, self.ports)

        assert port is not None
        return port.port_no

    def get_edge_to_core_port(self):
        def f(x, switch): return switch.name == 'int-br-ex' and switch or x
        port = reduce(f, self.ports)

        assert port is not None
        return port.port_no

    def get_port_by_name(self, port_name):
        for port in self.ports:
            if port.name == port_name:
                return port


class Flow(object):
    def __init__(self, *args, **kwargs):
        self.switch: Switch = kwargs.get('switch', None)
        self.table = kwargs.get('table', 0)
        self.priority = kwargs.get('priority', 101)
        self.match = kwargs.get('match', {})
        self.actions = kwargs.get('actions', [])

    def __repr__(self):
        return 'Flow {}'.format(self.__dict__)

    def get_flow(self):
        return {
            "dpid": int(self.switch.dpid, 16),
            "table_id": self.table,
            "cookie": 1,
            "priority": self.priority,
            "match": self.match,
            "instructions": [
                {
                    "type": "APPLY_ACTIONS",
                    "actions": self.actions
                }
            ],
            "actions": self.actions
        }

    def set_match(self, match):
        self.match = match

    def set_actions(self, actions):
        self.actions = actions

    def get_match(self):
        return self.match

    def get_actions(self):
        return self.actions

    def add_match(self, match_type, *argv):
        if match_type == 'tcp_src':
            self.match["tcp_src"] = argv[0]
            self.match["ip_proto"] = 6
            self.match["eth_type"] = 2048
        elif match_type == 'tcp_dst':
            self.match["tcp_dst"] = argv[0]
            self.match["ip_proto"] = 6
            self.match["eth_type"] = 2048
        elif match_type == 'udp_src':
            self.match["udp_src"] = argv[0]
            self.match["ip_proto"] = 17
            self.match["eth_type"] = 2048
        elif match_type == 'udp_dst':
            self.match["udp_dst"] = argv[0]
            self.match["ip_proto"] = 17
            self.match["eth_type"] = 2048
        elif match_type == 'ipv4_src':
            self.match["ipv4_src"] = argv[0]
            self.match["eth_type"] = 2048
        elif match_type == 'ipv4_dst':
            self.match["ipv4_dst"] = argv[0]
            self.match["eth_type"] = 2048
        elif match_type == 'arp_op':
            self.match["arp_op"] = 3
            self.match["eth_type"] = 2054
        elif match_type == "arp_spa":
            self.match["arp_spa"] = argv[0]
            self.match["eth_type"] = 2054
        elif match_type == "arp_tpa":
            self.match["arp_tpa"] = argv[0]
            self.match["eth_type"] = 2054
        elif match_type == "arp_tha":
            self.match["arp_tha"] = argv[0]
            self.match["eth_type"] = 2054
        elif match_type == 'ip_proto':
            self.match["ip_proto"] = 5
            self.match["eth_type"] = 34525
        elif match_type == 'icmpv4_type':
            # self.match["icmpv4_type"] = 5
            self.match["ip_proto"] = 1
            self.match["eth_type"] = 2048
        elif match_type == 'eth_dst':
            self.match["eth_dst"] = argv[0]
            self.match["eth_type"] = 2048
        elif match_type == 'eth_src':
            self.match["eth_src"] = argv[0]
            self.match["eth_type"] = 2048
        elif match_type == 'in_port':
            self.match["in_port"] = argv[0]
        elif match_type == "mpls_label":
            self.match["mpls_label"] = argv[0]
            self.match["eth_type"] = 34887
        return self.match

    def add_action(self, action_type, *argv):
        if action_type == 'OUTPUT':
            # Output packet from "port"
            self.actions.append(
                {"type": "OUTPUT", "port": argv[0]}
            )
        elif action_type == 'COPY_TTL_OUT':
            # Copy TTL outwards
            self.actions.append(
                {"type": "COPY_TTL_OUT"}
            )
        elif action_type == 'COPY_TTL_IN':
            # Copy TTL inwards
            self.actions.append(
                {"type": "COPY_TTL_IN"}
            )
        elif action_type == 'SET_MPLS_TTL':
            # Set MPLS TTL using "mpls_ttl"
            self.actions.append(
                {"type": "SET_MPLS_TTL", "mpls_ttl": 64}
            )
        elif action_type == 'DEC_MPLS_TTL':
            # Decrement MPLS TTL
            self.actions.append(
                {"type": "DEC_MPLS_TTL"}
            )
        elif action_type == 'PUSH_VLAN':
            # Push a new VLAN tag with "ethertype"
            self.actions.append(
                {"type": "PUSH_VLAN", "ethertype": 33024}
            )
        elif action_type == 'POP_VLAN':
            # Pop the outer VLAN tag
            self.actions.append(
                {"type": "POP_VLAN"}
            )
        elif action_type == 'PUSH_MPLS':
            # Push a new MPLS tag with "ethertype"
            self.actions.append(
                {"type": "PUSH_MPLS", "ethertype": 34887}
            )
        elif action_type == 'POP_MPLS':
            # Pop the outer MPLS tag with "ethertype"
            self.actions.append(
                {"type": "POP_MPLS", "ethertype": 2048}
            )
        elif action_type == 'SET_QUEUE':
            # Set queue id using "queue_id" when outputting to a port
            self.actions.append(
                {"type": "SET_QUEUE", "queue_id": 7}
            )
        elif action_type == 'GROUP':
            # Apply group identified by "group_id"
            self.actions.append(
                {"type": "GROUP", "group_id": 5}
            )
        elif action_type == 'SET_NW_TTL':
            # Set IP TTL using "nw_ttl"
            self.actions.append(
                {"type": "SET_NW_TTL", "nw_ttl": 64}
            )
        elif action_type == 'DEC_NW_TTL':
            # Decrement IP TTL
            self.actions.append(
                {"type": "DEC_NW_TTL"}
            )
        elif action_type == 'SET_FIELD':
            # Set a "field" using "value" (The set of keywords available for "field" is the same as match field)
            # See Example of set-field action
            action = {
                "type": "SET_FIELD",
                # Ex: Set VLAN_VID, VLAN_PCP, eth_src, eth_src, ipv4_src, ipv4_dst, mpls_label
                "field": argv[0],
                # Describe sum of vlan_id(e.g. 6) | OFPVID_PRESENT(0x1000=4096)
                "value": argv[1]
            }
            self.actions.append(action)
        elif action_type == 'PUSH_PBB':
            # Push a new PBB service tag with "ethertype" (Openflow1.3+)
            self.actions.append(
                {"type": "PUSH_PBB", "ethertype": 35047}
            )
        elif action_type == 'POP_PBB':
            # Pop the outer PBB service tag (Openflow1.3+)
            self.actions.append(
                {"type": "POP_PBB"}
            )
        elif action_type == 'COPY_FIELD':
            # Copy value between header and register (Openflow1.5+)
            self.actions.append(
                {"type": "COPY_FIELD", "n_bits": 32, "src_offset": 1,
                    "dst_offset": 2, "src_oxm_id": "eth_src", "dst_oxm_id": "eth_dst"}
            )
        elif action_type == 'METER':
            # Apply meter identified by "meter_id" (Openflow1.5+)
            self.actions.append(
                {"type": "METER", "meter_id": 3}
            )
        elif action_type == 'EXPERIMENTER':
            # Extensible action for the experimenter (Set "base64" or "ascii" to "data_type" field)
            self.actions.append(
                {"type": "EXPERIMENTER", "experimenter": 101,
                    "data": "AAECAwQFBgc=", "data_type": "base64"}
            )
        elif action_type == 'GOTO_TABLE':
            # (Instruction) Setup the next table identified by "table_id"
            self.actions.append(
                {"type": "GOTO_TABLE", "table_id": 8}
            )
        elif action_type == 'WRITE_METADATA':
            # (Instruction) Setup the metadata field using "metadata" and "metadata_mask"
            self.actions.append(
                {"type": "WRITE_METADATA", "metadata": 0x3, "metadata_mask": 0x3}
            )
        elif action_type == 'METER':
            # (Instruction) Apply meter identified by "meter_id" (deprecated in Openflow1.5)
            self.actions.append(
                {"type": "METER", "meter_id": 3}
            )
        elif action_type == 'WRITE_ACTIONS':
            # (Instruction) Write the action(s) onto the datapath action set
            self.actions.append(
                {"type": "WRITE_ACTIONS", "actions": [
                    {"type": "POP_VLAN", }, {"type": "OUTPUT", "port": 2}]}
            )
        elif action_type == 'CLEAR_ACTIONS':
            #   self.actions.append((Instruction) Clears all actions the datapath action set
            self.actions.append(
                {"type": "CLEAR_ACTIONS"}
            )

        return self.actions
