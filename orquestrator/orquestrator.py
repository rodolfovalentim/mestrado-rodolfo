# from models import VirtualFunction
import daiquiri
import logging
from collections import namedtuple
from nfv import FowardingGraphDomain, FowardingGraphHop, VirtualNetworkFunction
from switch import Flow, Link, Switch
from pprint import pprint
import queue

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)


def create_switch_graph(cloud):
    switches = get_switches(cloud)
    graph = GraphUndirectedWeighted(switches)
    for link in get_links(cloud):
        graph.add_edge(link.port_src.dpid, link.port_dst.dpid, 1)
    return graph


def get_hop_route(graph, edge_source, edge_destination):
    return graph.dijkstra(edge_source, edge_destination)


def create_virtual_function(cloud, name, availability_zone, vnf_type, may_exist=False):
    image = "ubuntu"
    flavor = "m1.small"
    network = "physnet1"
    vnf = cloud.create_virtual_machine(
        name, image, flavor, network, availability_zone=availability_zone, may_exist=may_exist)
    vnf.__class__ = VirtualNetworkFunction
    vnf.vnf_type = vnf_type
    vnf.cloud = cloud
    return vnf


def find_switch(cloud, ip):
    vm_taps = cloud.get_vm_ports()

    # Find tap if source is a VM
    target_tap: Tap = None
    for tap in vm_taps:
        if tap.ip == ip:
            target_tap = tap
            break

    # Find switch if source is not a VM
    switch_data = None
    if target_tap is None:
        switch_data = cloud.external_controller.get_datapath_id(
            ip)

        if(switch_data is None):
            logger.warning("ip to path return fail, discovering network")
            cloud.external_controller.discover_subrede(
                ip, '255.255.255.0')
            switch_data = cloud.external_controller.get_datapath_id(
                ip)

    logger.info(switch_data)
    logger.info(target_tap)

    switches = get_switches(cloud)

    assert switches is not None

    target_switch = None
    if target_tap is not None:
        for switch in switches:
            if switch.has_port(target_tap.name):
                target_switch = switch

    if switch_data is not None:
        for switch in switches:
            if switch.dpid == switch_data['dpid']:
                target_switch = switch

    return target_switch


def create_chain(flow_classifier, service_chain, simetric=False):
    
    fgds = [FowardingGraphDomain()]
    fgds[-1].nfvi_pop = flow_classifier["source_cloud"]
    fgds[-1].hops.append(FowardingGraphHop())
    
    source_switch = find_switch(flow_classifier["source_cloud"], flow_classifier["source_ip"])    
    fgds[-1].hops[-1].src_edge_switch = source_switch
    
    for vnf in service_chain:
        if fgds[-1].nfvi_pop.get_name() != vnf.get_cloud().get_name():
            fgds.append(FowardingGraphDomain())
            fgds[-1].nfvi_pop = flow_classifier["source_cloud"]
            fgds[-1].hops.append(FowardingGraphHop())
            
        target_switch = find_switch(vnf.get_cloud(), vnf.get_ip())
        fgds[-1].hops[-1].dest_vnf = vnf
        fgds[-1].hops[-1].dest_edge_switch = target_switch
        fgds[-1].hops.append(FowardingGraphHop(src_vnf=vnf))
        fgds[-1].hops[-1].src_edge_switch = target_switch
    
    destination_switch = find_switch(flow_classifier["destination_cloud"], flow_classifier["destination_ip"]) 
    fgds[-1].hops[-1].dest_edge_switch = destination_switch
    
    for fgd in fgds:
        for hop in fgd.hops:
            if hop.src_vnf is None:
                if fgd.prev_fgd is None:
                    hop.set_flow_classifier(flow_classifier)
                else:
                    hop.set_src_gateway(src_vnf.get_cloud())
                
            if hop.dest_vnf is None:
                if fgd.next_fgd is None:
                    hop.set_flow_destination()
                else:
                    hop.set_dest_gateway(src_vnf.get_cloud())
                    
            hop.create_flows()
            hop.install_flows()
                           
    # chain_per_domain = []
    # current_fgd = FowardingGraphDomain()
    
    # if service_chain != []:
    #     current_fgd.nfvi_pop = service_chain[0].get_cloud()
    
    # for vnf in service_chain:
    #     if current_fgd.nfvi_pop.get_name() != vnf.get_cloud().get_name():
    #         chain_per_domain.append(current_fgd)
    #         current_fgd = FowardingGraphDomain()
    #         current_fgd.nfvi_pop = vnf.get_cloud()
            
    #         # Saving references
    #         current_fgd.prev_fgd = chain_per_domain[-1]
    #         chain_per_domain[-1].next_fgd = current_fgd
            
    #     current_hop = FowardingGraphHop(dest_vnf=vnf)
    #     if len(current_fgd.intradomain_hops) > 0:
    #         current_hop.src_vnf = current_fgd.intradomain_hops[-1].dest_vnf
            
    #     current_fgd.intradomain_hops.append(current_hop)
    #     # current_fgd.ordered_vnfs.append(vnf)
    # chain_per_domain.append(current_fgd)

    # for chain in chain_per_domain:
    #     for hop in chain.intradomain_hops:
    #         if hop.prev_hop is None and chain.prev_fgd is None:
    #             # primeiro salto de todos. eh preciso ter o classificador de fluxo
                
    #         if hop.next_hop is None and chain.next_fgd is None:
    #             # ultimo salto de todos, restaurar o pacote para o original
                
    #         if hop.prev_hop is None and chain.prev_fgd is not None:
    #             # primeiro salto de um dominio, tem que buscar no gateway
            
    #         if hop.next_hop is None and chain.next_fgd is not None:
    #             # ultimo salto de um dominio, tem que mandar para um gateway

def get_switches(cloud):    
    all_switches = cloud.topology_controller.get_switches()

    assert all_switches is not None

    d_switches = {}

    d_switches['edge'] = {
        switch['dpid']: switch for switch in cloud.edge_controller.get_switches()}

    d_switches['core'] = {
        switch['dpid']: switch for switch in cloud.core_controller.get_switches()}

    d_switches['external'] = {
        switch['dpid']: switch for switch in cloud.external_controller.get_switches()}

    assert d_switches['edge'] is not None
    assert d_switches['core'] is not None
    assert d_switches['external'] is not None

    switches = []

    for switch in all_switches:
        sw = Switch(**switch)

        if sw.dpid in d_switches['core'].keys():
            sw.switch_type = 'core'
            core_sw = cloud.core_controller.get_switch(sw.dpid)
            if core_sw:
                sw.key = core_sw.get('key')
        elif sw.dpid in d_switches['edge'].keys():
            sw.switch_type = 'edge'
        elif sw.dpid in d_switches['external'].keys():
            sw.switch_type = 'external'

        switches.append(sw)

    return switches

def get_links(cloud):
    r_links = cloud.topology_controller.get_links()

    links = []

    if r_links is None or len(r_links) < 0:
        return links

    for link in r_links:
        links.append(Link(**link))

    return links

def get_gateway_switch(cloud):
    all_switches = cloud.topology_controller.get_switches()

    if(all_switches is None):
        logger.error(
            "Some Error occur during topology discovery. Check controllers and network")
        return

    d_switches = {
        switch['dpid']: switch for switch in cloud.gateway_controller.get_switches()}

    switch = None
    for switch in all_switches:
        sw = Switch(**switch)
        if sw.dpid in d_switches.keys():
            sw.switch_type = 'gateway'
            return switch

    assert switch is not None
    return


Edge = namedtuple('Edge', ['vertex', 'weight'])


class GraphUndirectedWeighted(object):
    def __init__(self, switches):
        self.switches = switches
        self.switches_count = len(switches)
        self.adjacency_list = [[] for _ in range(len(switches))]

    def __repr__(self):
        return "< Cloud Graph {} >".format(self.__dict__)
        

    def add_edge(self, source_dpid, dest_dpid, weight):
        source = [x.dpid for x in self.switches].index(source_dpid)
        dest = [x.dpid for x in self.switches].index(dest_dpid)
        self.adjacency_list[source].append(Edge(dest, weight))
        self.adjacency_list[dest].append(Edge(source, weight))

    def get_edge(self, vertex):
        for e in self.adjacency_list[vertex]:
            yield e

    def get_vertex(self):
        for v in range(self.switches_count):
            yield v

    def dijkstra(self, source, dest):        
        source = [x.dpid for x in self.switches].index(source.dpid)
        dest = [x.dpid for x in self.switches].index(dest.dpid)

        q = queue.PriorityQueue()
        parents = []
        distances = []
        start_weight = float("inf")

        for i in self.get_vertex():
            weight = start_weight
            if source == i:
                weight = 0
            distances.append(weight)
            parents.append(None)

        q.put(([0, source]))

        while not q.empty():
            v_tuple = q.get()
            v = v_tuple[1]

            for e in self.get_edge(v):
                candidate_distance = distances[v] + e.weight
                if distances[e.vertex] > candidate_distance:
                    distances[e.vertex] = candidate_distance
                    parents[e.vertex] = v
                    # primitive but effective negative cycle detection
                    if candidate_distance < -1000:
                        raise Exception("Negative cycle detected")
                    q.put(([distances[e.vertex], e.vertex]))

        shortest_path = []
        end = dest
        while end is not None:
            shortest_path.append(self.switches[end])
            end = parents[end]

        shortest_path.reverse()

        return shortest_path, distances[dest]
