from functools import reduce

class Port(object):
    def __init__(self, *args, **kwargs):
        self.dpid = kwargs.get('dpid', None)
        self.port_no = kwargs.get('port_no', None)
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
        self.ports = [Port(**port) for port in kwargs.get('ports')]
        self.switch_type = kwargs.get('switch_type', 'default')

        if (self.switch_type == 'core'):
            self.key = kwargs.get('key', None)

    def __repr__(self):
        return 'Switch {}'.format(self.__dict__)

    def get_dpid(self):
        return self.dpid

    def set_dpid(self, dpid):
        self.dpid = dpid

    def add_port(self, port):
        self.ports.append(port)

    def set_ports(self, ports):
        self.ports = ports

    def has_port(self, name):
        for port in self.ports:
            if port.name == name:
                return True
        return False

    def get_core_to_edge_port(self):
        if self.switch_type == 'external':
            f = lambda x, switch: switch.name == '{}-to-core'.format(switch.dpid[-4:]) and switch or x
        else:
            f = lambda x, switch: switch.name == 'int-br-ex' and switch or x 
        port = reduce(f, self.ports)
        
        assert port is not None        
        return port.port_no

    def get_edge_to_core_port(self):
        if self.switch_type == 'external':
            f = lambda x, switch: switch.name == '{}-to-core'.format(switch.dpid[-4:]) and switch or x
        else:
            f = lambda x, switch: switch.name == 'int-br-ex' and switch or x 
        port = reduce(f, self.ports)
        
        assert port is not None        
        return port.port_no


class Flow(object):
    def __init__(self, *args, **kwargs):
        self.switch: Switch = kwargs.get('switch', None)
        self.table = kwargs.get('switch', None)
        self.priority = kwargs.get('priority', 0)
        self.match = kwargs.get('match', {})
        self.actions = kwargs.get('actions', [])

    def __repr__(self):
        return 'Switch {}'.format(self.__dict__)

    def get_flow(self):
        return {
            "dpid": self.switch.dpid,
            "table": self.table,
            "priority": self.priority,
            "match": self.match,
            "actions": self.actions
        }

    def add_match(self, match_type, *argv):
        if match_type == 'in_port':
            self.match['in_port'] = argv[0]
        elif match_type == 'dl_src':
            self.match['dl_src'] = argv[0]
        elif match_type == 'dl_dst':
            self.match['dl_dst'] = argv[0]
        elif match_type == 'dl_vlan':
            self.match['dl_vlan'] = argv[0]
        elif match_type == 'dl_vlan_pcp':
            self.match['dl_vlan_pcp'] = argv[0]
            self.match['dl_vlan'] = argv[1]
        elif match_type == 'dl_type':
            self.match['dl_type'] = argv[0]
        elif match_type == 'nw_tos':
            self.match['nw_tos'] = argv[0]
        elif match_type == 'nw_proto':
            self.match['nw_proto'] = argv[0]
            self.match['dl_type'] = 2048
        elif match_type == 'nw_src':
            self.match['nw_src'] = argv[0]
            self.match['dl_type'] = 2048
        elif match_type == 'nw_dst':
            self.match['nw_dst'] = argv[0]
            self.match['dl_type'] = 2048
        elif match_type == 'tp_src':
            self.match['tp_src'] = argv[0]
            self.match['dl_type'] = 2048
        elif match_type == 'tp_dst':
            self.match['nw_proto'] = argv[0]
            self.match['tp_dst'] = argv[1]
            self.match['dl_type'] = 2048
        elif match_type == 'udp_dst':
            self.match['udp_dst'] = argv[0]
            self.match['ip_proto'] = 17
            self.match['eth_type'] = 2048
        return self.match

    def add_action(self, action_type, *argv):
        if action_type == 'OUTPUT':
            self.actions.append({'type': 'OUTPUT', 'port': argv[0]})
        elif action_type == 'SET_VLAN_VID':
            self.actions.append({'type': 'SET_VLAN_VID', 'vlan_vid': argv[0]})
        elif action_type == 'SET_VLAN_PCP':
            self.actions.append({'type': 'SET_VLAN_PCP', 'vlan_pcp': argv[0]})
        elif action_type == 'STRIP_VLAN':
            self.actions.append({'type': 'STRIP_VLAN'})
        elif action_type == 'SET_DL_SRC':
            self.actions.append({'type': 'SET_DL_SRC', 'dl_src': argv[0]})
        elif action_type == 'SET_DL_DST':
            self.actions.append({'type': 'SET_DL_DST', 'dl_dst': argv[0]})
        elif action_type == 'SET_NW_SRC':
            self.actions.append({'type': 'SET_NW_SRC', 'nw_src': argv[0]})
        elif action_type == 'SET_NW_DST':
            self.actions.append({'type': 'SET_NW_DST', 'nw_dst': argv[0]})
        elif action_type == 'SET_NW_TOS':
            self.actions.append({'type': 'SET_NW_TOS', 'nw_tos': argv[0]})
        elif action_type == 'SET_TP_SRC':
            self.actions.append({'type': 'SET_TP_SRC', 'tp_src': argv[0]})
        elif action_type == 'SET_TP_DST':
            self.actions.append({'type': 'SET_TP_DST', 'tp_dst': argv[0]})
        elif action_type == 'ENQUEUE':
            self.actions.append(
                {'type': 'ENQUEUE', 'queue_id': argv[0], 'port': argv[1]})

        return self.actions