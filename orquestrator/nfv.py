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

class DomainForwardingGraph(object):
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
        
        self.flow_classifier = kwargs.get('flow_classifier', None)
        self.flow_destination = kwargs.get('flow_destination', None)

        self.flows = kwargs.get('flows', [])

        self.src_vnf = kwargs.get('src_vnf', None)
        self.src_edge_switch = kwargs.get('src_edge_switch', None)
        self.src_gateway = kwargs.get('src_gateway', None)
        
        self.dest_vnf = kwargs.get('dest_vnf', None)
        self.dest_edge_switch = kwargs.get('dest_edge_switch', None)
        self.dest_gateway = kwargs.get('dest_gateway', None)
        
        
    def __repr__(self):
        return "< Fowarding Graph Hop {} >".format(self.__dict__)
    
    def create_flow_classifier(self, flow_classifier):
        self.flow_classifier = Flow()
        self.flow_classifier.add_match('ipv4_src', flow_classifier['source_ip'])
        self.flow_classifier.add_match('ipv4_dst', flow_classifier['destination_ip'])
        
        if flow_classifier['protocol'] == 'udp':
            self.flow_classifier.add_match('udp_src', flow_classifier['source_port'])
            self.flow_classifier.add_match('udp_dst', flow_classifier['destination_port'])
        elif flow_classifier['protocol'] == 'tcp':
            self.flow_classifier.add_match('tcp_src', flow_classifier['source_port'])
            self.flow_classifier.add_match('tcp_dst', flow_classifier['destination_port'])
        elif flow_classifier['protocol'] == 'icmp':
            self.flow_classifier.add_match('icmpv4_type')
        elif flow_classifier['protocol'] == 'ip':
            self.flow_classifier.add_match('ip_proto')
        elif flow_classifier['protocol'] == 'arp':
            self.flow_classifier.add_match('arp_op')

    def create_flow_destination(self):
        self.flow_destination = Flow()
        self.flow_destination.add_action("SET_DL_DST", self.dest_vnf.ip[0].mac_address)
        self.flow_destination.add_action("OUTPUT", self.dest_edge_switch.get_port_by_name(self.dest_vnf.ip[0].name).port_no)

    def create_graph(self, domain_graph):
        if self.src_edge_switch != self.dest_edge_switch:
            self.hop_id = domain_graph.dijkstra(src_edge_switch, dest_edge_switch)

    def create_flows(self, method):
        if self.src_edge_switch == self.dest_edge_switch:
            flow = None
            if self.flow_classifier is not None:
                flow = self.flow_classifier
            else:
                flow = Flow()
                port_name = self.prev_hop.dest_vnf.get_port()
                in_port = self.prev_hop.dest_edge_switch.get_port_by_name(port_name)
                flow.add_match("dl_dst", self.prev_hop.id)
                flow.add_match("in_port", in_port)

            if self.flow_destination is not None:
                flow = self.flow_destination
                flow.add_action("SET_DL_DST", self.hop_id)
            else:
                flow = Flow()
                dest_port_name = self.dest_vnf.get_port()
                output_port = self.dest_edge_switch.get_port_by_name(port_name)
                flow.add_action('OUTPUT', self.src_edge_switch.get_port_by_name("phy-br-ex"))
                flow.add_action("SET_DL_DST", self.hop_id)
                flow.add_action("OUTPUT", output_port)

            self.flows.append(flow)
               
        elif self.src_edge_switch != self.dest_edge_switch:
            src_flow = None
            if self.flow_classifier is not None:
                src_flow = self.flow_classifier
            else:          
                src_flow = Flow()
                src_flow.add_match("dl_dst", self.prev_hop.id)
                src_flow.add_match("in_port", in_port)
                src_flow.add_action('OUTPUT', self.src_edge_switch.get_port_by_name("phy-br-ex"))
                src_flow.add_action("SET_DL_DST", self.hop_id)

            self.flows.append(src_flow)

            dest_flow = None
            if self.flow_destination is not None:
                flow = self.flow_destination
                flow.add_action("SET_DL_DST", self.hop_id)
            else:
                dest_flow = Flow()            
                dest_port_name = self.dest_vnf.get_port()
                output_port = self.dest_edge_switch.get_port_by_name(port_name)
                dest_flow.add_match("dl_dst", self.hop_id)
                dest_flow.add_action("OUTPUT", output_port)

            self.flows.append(dest_flow)

    def install_flows(self):
       for flow in self.flows:
           flow.install()
