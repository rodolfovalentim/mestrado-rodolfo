from .cloud import VirtualMachine
from .switch import Flow

from netaddr import EUI
from functools import reduce
from netaddr.strategy.eui48 import mac_unix_expanded

import daiquiri
import logging

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)


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
        self.arp_flows = kwargs.get('arp_flows', [])

    def __repr__(self):
        return "< Fowarding Graph Domain {} >".format(self.__dict__)

    def install_arp_flow(self):
        for flow in self.arp_flows:
            logging.info(self.nfvi_pop)
            self.nfvi_pop.edge_controller.add_arp_reply(flow)

    def remove_arp_flow(self):
        for flow in self.arp_flows:
            logging.info(self.nfvi_pop)
            self.nfvi_pop.edge_controller.del_arp_reply(flow)

    def create_arp(self, src_vm, dst_vm):
        self.arp_flows.append(Flow())
        self.arp_flows[-1].switch = self.hops[0].src_switch
        src_port_no = self.hops[0].dest_switch.get_port_by_name(src_vm.get_tap().get_name()).port_no
        self.arp_flows[-1].add_match("in_port", src_port_no)
        self.arp_flows[-1].add_match("arp_tpa", dst_vm.get_tap().get_ip())
        self.arp_flows[-1].add_match("arp_tha", dst_vm.get_tap().get_mac_address())


class ForwardingGraphHop(object):
    def __init__(self, *args, **kwargs):
        self.switch_graph = kwargs.get('switch_graph', None)
        self.prev_hop = kwargs.get('prev_hop', None)
        self.next_hop = kwargs.get('next_hop', None)
        self.hop_id = kwargs.get('hop_id', None)
        self.hop_type = kwargs.get('hop_type', HopClassification())

        self.flow_classifier = kwargs.get('flow_classifier', None)
        self.flow_destination = kwargs.get('flow_destination', None)

        self.flows = kwargs.get('flows', [])

        self.src_tap = kwargs.get('src_tap', None)
        self.src_switch = kwargs.get('src_switch', None)
        
        self.dest_tap = kwargs.get('dest_tap', None)
        self.dest_switch = kwargs.get('dest_switch', None)
        
        self.keys = []
        self.ports = []
        
    def __repr__(self):
        return "< Fowarding Graph Hop {} >".format(self.__dict__)
    
    def create_flow_classifier(self, flow_classifier):
        self.flow_classifier = Flow()

        if flow_classifier['protocol'] != 'arp':
            self.flow_classifier.add_match('ipv4_src', flow_classifier['source_ip'])
            self.flow_classifier.add_match('ipv4_dst', flow_classifier['destination_ip'])
        
        if flow_classifier['protocol'] == 'udp':
            if flow_classifier.get('source_port', None) is not None:
                self.flow_classifier.add_match('udp_src', flow_classifier['source_port'])
            if flow_classifier.get('destination_port', None) is not None:
                self.flow_classifier.add_match('udp_dst', flow_classifier['destination_port'])
        elif flow_classifier['protocol'] == 'tcp':
            if flow_classifier.get('source_port', None) is not None:
                self.flow_classifier.add_match('tcp_src', flow_classifier['source_port'])
            if flow_classifier.get('destination_port', None) is not None:
                self.flow_classifier.add_match('tcp_dst', flow_classifier['destination_port'])
        elif flow_classifier['protocol'] == 'icmp':
            self.flow_classifier.add_match('icmpv4_type')
        elif flow_classifier['protocol'] == 'ip':
            self.flow_classifier.add_match('ip_proto')
            
        elif flow_classifier['protocol'] == 'arp':
            self.flow_classifier.add_match('arp_op')
            self.flow_classifier.add_match('arp_spa', flow_classifier['source_ip'])
            self.flow_classifier.add_match('arp_tpa', flow_classifier['destination_ip'])

    def create_flow_destination(self, destination):
        self.flow_destination = Flow()
        self.flow_destination.add_action("SET_FIELD", "eth_dst", destination.get_tap().get_mac_address())
        self.flow_destination.add_action("OUTPUT", self.dest_switch.get_port_by_name(destination.get_tap().get_name()).port_no)

    def create_graph(self, domain_graph):
        if self.src_switch.dpid != self.dest_switch.dpid:
            self.switch_graph = domain_graph.dijkstra(self.src_switch, self.dest_switch)[1:]
 
    def get_keyflow_data(self, adjmatrix):
        if self.switch_graph is None:
            return
            
        logging.warning('Keyflow')
        logging.warning(self.switch_graph)
        hops = zip(self.switch_graph[0:-1], self.switch_graph[1:]) 
        for hop in hops:
            logging.warning(int(hop[0].key))
            logging.warning(hop[0].dpid)
            logging.warning(hop[1].dpid)
            logging.warning(int(adjmatrix.get(hop[0].dpid, hop[1].dpid).port_no))
            self.keys.append(int(hop[0].key))
            self.ports.append(int(adjmatrix.get(hop[0].dpid, hop[1].dpid).port_no))

    def create_flow(self):
        self.flows = [Flow()]
        self.flows[0].switch = self.src_switch
        self.flows[0].set_match(self.flow_classifier.get_match())
        self.flows[0].add_match('in_port', self.src_switch.get_port_by_name(self.src_tap.get_name()).port_no)
        
        if self.hop_type.same_host:
            self.flows[0].add_action("SET_FIELD", "eth_dst", self.dest_tap.get_mac_address())
            self.flows[0].add_action("OUTPUT", self.flows[0].switch.get_port_by_name(self.dest_tap.get_name()).port_no)
            return
        
        self.flows[0].add_action("SET_FIELD", "eth_dst", self.hop_id)
        self.flows[0].add_action("OUTPUT", self.flows[0].switch.get_edge_to_core_port())
        
        self.flows += [Flow()]
        self.flows[-1].switch = self.dest_switch
        self.flows[-1].add_match('in_port', self.flows[-1].switch.get_core_to_edge_port())
        self.flows[-1].add_match('eth_dst', self.hop_id)

        self.flows[-1].add_action("SET_FIELD", "eth_dst", self.dest_tap.get_mac_address())
        self.flows[-1].add_action("OUTPUT", self.flows[-1].switch.get_port_by_name(self.dest_tap.get_name()).port_no)        

class HopClassification(object):
    def __init__(self):
        super().__init__()
        self.same_host = False
        self.first_hop = False
        self.last_hop = False
        self.from_gateway = False
        self.to_gateway = False
    
    def __repr__(self):
        return 'Hop Classification {}'.format(self.__dict__)


class AdjacencyMatrix(object):
    matrix = {}

    def __init__(self, links):
        super().__init__()
        for link in links:
            if self.matrix.get(link.port_src.dpid) is None:
                self.matrix[link.port_src.dpid] = { link.port_dst.dpid: link.port_src }
            else:
                self.matrix[link.port_src.dpid][link.port_dst.dpid] = link.port_src 

    def get(self, src, dst):
        return self.matrix.get(src).get(dst)


class KeyFlow(object):

    code = "90"

    @staticmethod
    def chinese_remainder(n, a):

        assert len(n) == len(a)
        
        if len(n) == 0:
            return 0

        sum = 0
        prod = reduce(lambda a, b: a * b, n)

        for n_i, a_i in zip(n, a):
            p = prod // n_i
            sum += a_i * KeyFlow.mul_inv(p, n_i) * p
        return sum % prod

    @staticmethod
    def mul_inv(a, b):
        b0 = b
        x0 = 0
        x1 = 1
        if b == 1: return 1
        while a > 1:
            q = a // b
            a, b = b, a % b
            x0, x1 = x1 - q * x0, x0
        if x1 < 0:
            x1 += b0
        return x1

    @staticmethod
    def encode(key):
        hex_key = hex(key)
        mac_address = int(hex_key + '0000', 16)
        mac = EUI(mac_address)
        mac[0] = 0x90
        mac.dialect = mac_unix_expanded
        key = str(mac)
        return key

    # print(chinese_remainder([11, 19], [7, 5]), hex(chinese_remainder([11, 19], [7, 5])))
