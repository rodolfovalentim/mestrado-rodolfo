from .cloud import VirtualMachine
from .switch import Flow

class VirtualNetworkFunction(VirtualMachine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nf_type = kwargs.get('nf_type', None)
        self.nfvi_pop = kwargs.get('nfvi_pop', None)
    
    def __repr__(self):
        return 'Virtual Machine {}'.format(self.__dict__)

    def get_ip(self):
        if len(self.taps) > 0:
            return self.taps[0].get_ip()

    def get_cloud(self):
        return self.cloud

class FowardingGraphDomain(object):
    '''
        Graph inside domain
    '''
    def __init__(self, *args, **kwargs):
        # self.id = kwargs.get('id', None)
        self.nfvi_pop = kwargs.get('nfvi_pop', None)
        self.prev_fgd = kwargs.get('prev_fgd', None)      
        self.next_fgd = kwargs.get('next_fgd', None)
        self.domain_graph =  kwargs.get('domain_graph', None)
        self.hops = kwargs.get('hops', [])
        
    def __repr__(self):
        return "< Fowarding Graph Domain {} >".format(self.__dict__)
        
class FowardingGraphHop(object):
    def __init__(self, *args, **kwargs):
        self.switch_graph = kwargs.get('switch_graph', None)
        self.prev_hop = kwargs.get('prev_hop', None)
        self.next_hop = kwargs.get('next_hop', None)
        self.hop_id = kwargs.get('hop_id', None)
        
        self.src_flow = kwargs.get('src_flow', Flow())
        self.src_vnf = kwargs.get('src_vnf', None)
        self.src_edge_switch = kwargs.get('src_edge_switch', None)
        self.src_external_switches = kwargs.get('src_external_switches', [])
        self.src_gateway = kwargs.get('src_gateway', None)
        
        self.dest_flow = kwargs.get('dest_flow', Flow())
        self.dest_vnf = kwargs.get('dest_vnf', None)
        self.dest_edge_switch = kwargs.get('dest_edge_switch', None)
        self.dest_external_switches = kwargs.get('dest_external_switches', [])
        self.dest_gateway = kwargs.get('dest_gateway', None)
        
        
    def __repr__(self):
        return "< Fowarding Graph Hop {} >".format(self.__dict__)
    
    def set_flow_classifier(self, flow_classifier):
        self.src_flow.add_match('ipv4_src', flow_classifier['source_ip'])
        self.src_flow.add_match('ipv4_dst', flow_classifier['destination_ip'])
        
        if flow_classifier['protocol'] == 'udp':
            self.src_flow.add_match('udp_src', flow_classifier['source_port'])
            self.src_flow.add_match('udp_dst', flow_classifier['destination_port'])
        elif flow_classifier['protocol'] == 'tcp':
            self.src_flow.add_match('tcp_src', flow_classifier['source_port'])
            self.src_flow.add_match('tcp_dst', flow_classifier['destination_port'])
        elif flow_classifier['protocol'] == 'icmp':
            self.src_flow.add_match('icmpv4_type')
        elif flow_classifier['protocol'] == 'ip':
            self.src_flow.add_match('ip_proto')
        elif flow_classifier['protocol'] == 'arp':
            self.src_flow.add_match('arp_op')

    def set_flow_destination(self):
        if self.dest_vnf is not None:
            self.dest_flow = Flow()
            self.add_action("SET_DL_DST", self.dest_vnf.ip[0].mac_address)
            # Fica ai o questinamento, eu devo fazer um output normal  ou fazer para a porta?
            self.add_action("OUTPUT", 65355)
            self.add_action("OUTPUT", self.dest_edge_switch.get_port_by_name(self.dest_vnf.ip[0].name).port_no)
            

    def create_flows(self):
        if self.

        if self.src_edge_switch == self.dest_edge_switch:
            pass
        else self.src_edge_switch != self.dest_edge_switch:
            pass    

    def install_flows(self):
        pass
