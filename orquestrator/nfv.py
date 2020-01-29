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
        self.flow_classifier = kwargs.get('flow_classifier', None)
        self.switch_graph = kwargs.get('switch_graph', None)
        self.prev_hop = kwargs.get('prev_hop', None)
        self.next_hop = kwargs.get('next_hop', None)
        self.hop_id = kwargs.get('hop_id', None)
        self.src_vnf = kwargs.get('src_vnf', None)
        self.dest_vnf = kwargs.get('dest_vnf', None)
        self.src_edge_switch = kwargs.get('src_edge_switch', None)
        self.dest_edge_switch = kwargs.get('dest_edge_switch', None)
        self.src_external_switches = kwargs.get('src_external_switches', [])
        self.dest_external_switches = kwargs.get('dest_external_switches', [])
        self.src_gateway = kwargs.get('src_gateway', None)
        self.dest_gateway = kwargs.get('dest_gateway', None)
        self.src_flow = kwargs.get('src_flow', None)
        self.dest_flow = kwargs.get('dest_flow', None)
        
    def __repr__(self):
        return "< Fowarding Graph Hop {} >".format(self.__dict__)
    
    def set_flow_classifier(self, flow_classifier):
        self.flow_classifier = Flow()
        self.add_match('ipv4_src', flow_classifier['source_ip'])
        self.add_match('ipv4_dst', flow_classifier['destination_ip'])
        
        if flow_classifier['protocol'] == 'udp':
            pass
        elif flow_classifier['protocol'] == 'tcp':
            pass
        elif flow_classifier['protocol'] == 'icmp':
            pass
        elif flow_classifier['protocol'] == 'ip':
            pass  
        elif flow_classifier['protocol'] == 'arp':
            pass
            

    def set_src_gateway(self):
        pass

    def set_flow_destination(self):
        pass

    def set_dest_gateway(self):
        pass

    def create_flows(self):
        pass

    def install_flows(self):
        pass
