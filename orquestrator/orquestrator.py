# from models import VirtualFunction
import daiquiri
import logging
from collections import namedtuple
from .nfv import DomainForwardingGraph, ForwardingGraphHop, VirtualNetworkFunction
from .switch import Flow, Link, Switch
from pprint import pprint
import queue
from orquestrator.nfv import AdjacencyMatrix, KeyFlow, NetworkingSFC, Sourcey
import random

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)


def create_switch_graph(cloud):
    switches = get_all_switches(cloud)
    graph = GraphUndirectedWeighted(switches)
    for link in get_all_links(cloud):
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

    # logger.info(target_tap)

    switches = get_edge_switches(cloud)
    logger.info(switches)

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


def create_chain(flow_classifier, service_chain, method='keyflow'):
    fgds = [DomainForwardingGraph()]
    fgds[-1].nfvi_pop = flow_classifier["source_cloud"]
    fgds[-1].domain_graph = create_domain_graph(fgds[-1].nfvi_pop)
    fgds[-1].hops.append(ForwardingGraphHop())

    source_switch = find_switch(
        flow_classifier["source_cloud"], flow_classifier["source_ip"])
    src_vm = flow_classifier["source_cloud"].find_virtual_machine_by_ip(
        flow_classifier["source_ip"])
    fgds[-1].hops[-1].src_tap = src_vm.get_tap()
    fgds[-1].hops[-1].src_switch = source_switch

    for vnf in service_chain:
        if fgds[-1].nfvi_pop.get_name() != vnf.get_cloud().get_name():
            fgds.append(DomainForwardingGraph(prev_fgd=fgds[-1]))
            fgds[-1].prev_fgd.next_fgd = fgds[-1]
            fgds[-1].nfvi_pop = vnf.get_cloud()
            fgds[-1].domain_graph = create_domain_graph(fgds[-1].nfvi_pop)
            fgds[-1].hops.append(ForwardingGraphHop(
                src_tap=fgds[-1].prev_fgd.hops[-1].dest_tap, prev_hop=fgds[-1].prev_fgd.hops[-1]))
            fgds[-1].hops[-1].prev_hop.next_hop = fgds[-1].prev_fgd.hops[-1]

        target_switch = find_switch(vnf.get_cloud(), vnf.get_ip())
        fgds[-1].hops[-1].dest_tap = vnf.get_tap()
        fgds[-1].hops[-1].dest_switch = target_switch
        fgds[-1].hops.append(ForwardingGraphHop(
            src_tap=fgds[-1].hops[-1].dest_tap, prev_hop=fgds[-1].hops[-1]))
        fgds[-1].hops[-1].prev_hop.next_hop = fgds[-1].hops[-1]
        fgds[-1].hops[-1].src_switch = target_switch

    if fgds[-1].nfvi_pop.get_name() != flow_classifier["destination_cloud"].get_name():
        fgds.append(DomainForwardingGraph(prev_fgd=fgds[-1]))
        fgds[-1].prev_fgd.next_fgd = fgds[-1]
        fgds[-1].nfvi_pop = flow_classifier["destination_cloud"]
        fgds[-1].domain_graph = create_domain_graph(fgds[-1].nfvi_pop)
        fgds[-1].hops.append(ForwardingGraphHop(
            src_tap=fgds[-1].prev_fgd.hops[-1].dest_tap, prev_hop=fgds[-1].prev_fgd.hops[-1]))
        fgds[-1].hops[-1].prev_hop.next_hop = fgds[-1].prev_fgd.hops[-1]

    dest_switch = find_switch(
        flow_classifier["destination_cloud"], flow_classifier["destination_ip"])
    dest_vm = flow_classifier["destination_cloud"].find_virtual_machine_by_ip(
        flow_classifier["destination_ip"])
    fgds[-1].hops[-1].dest_tap = dest_vm.get_tap()
    fgds[-1].hops[-1].dest_switch = dest_switch

    for fgd in fgds:
        for hop in fgd.hops:
            hop.create_flow_classifier(flow_classifier)
            if hop.src_tap is None and fgd.prev_fgd is not None:
                hop.src_switch = get_gateway_switches(fgd.nfvi_pop)[0]
                hop.hop_type.from_gateway = True

            if hop.dest_tap is None and fgd.next_fgd is not None:
                hop.dest_switch = get_gateway_switches(fgd.nfvi_pop)[0]
                hop.hop_type.to_gateway = True

            if hop.src_switch.dpid == hop.dest_switch.dpid:
                hop.hop_type.same_host = True

    for fgd in fgds:
        domain_links = get_all_links(fgd.nfvi_pop)
        adjmatrix = AdjacencyMatrix(domain_links)
        for idx, hop in enumerate(fgd.hops):
            hop.create_graph(fgd.domain_graph)
            hop.get_underlay_data(adjmatrix)

            if method == 'keyflow':
                key = KeyFlow.chinese_remainder(hop.keys, hop.ports)
                hop.hop_id = KeyFlow.encode(key)
            elif method == 'sourcey':
                hop.segment_id = Sourcey.rand_mac()
                hop.hop_id = Sourcey.encode(hop.ports)
            elif method == 'networking_sfc':
                hop.hop_id = idx + random.randint(200, 500)

            logging.warning(hop.hop_id)

    for fgd in fgds:
        for hop in fgd.hops:
            if method == 'keyflow':
                KeyFlow.create_flow(hop)
            elif method == 'sourcey':
                Sourcey.create_flow(hop)
            elif method == 'networking_sfc':
                NetworkingSFC.create_flow(hop)

        src_vm = flow_classifier["source_cloud"].find_virtual_machine_by_ip(
            flow_classifier["source_ip"])
        dst_vm = flow_classifier["destination_cloud"].find_virtual_machine_by_ip(
            flow_classifier["destination_ip"])

        if fgd.prev_fgd is None:
            fgd.create_arp(src_vm, dst_vm)

    for fgd in fgds:
        for hop in fgd.hops:
            logger.warning(hop.hop_type)

            for flow in hop.flows:
                logger.info(flow.get_flow())
                fgd.nfvi_pop.ofctl_controller.add_flow(flow.get_flow())

            # if hop.hop_type.from_gateway or hop.hop_type.to_gateway:
            #     if hop.hop_type.from_gateway:
            #         fgd.nfvi_pop.gateway_controller.add_flow(
            #             hop.flows[0].get_flow())
            #     else:
            #         fgd.nfvi_pop.ofctl_controller.add_flow(
            #             hop.flows[0].get_flow())

            #     if hop.hop_type.to_gateway:
            #         fgd.nfvi_pop.gateway_controller.add_flow(
            #             hop.flows[-1].get_flow())
            #     else:
            #         fgd.nfvi_pop.ofctl_controller.add_flow(
            #             hop.flows[-1].get_flow())

            #     for flow in hop.flows[1:-1]:
            #         fgd.nfvi_pop.ofctl_controller.add_flow(flow.get_flow())
            # else:
            #     for flow in hop.flows:
            #         fgd.nfvi_pop.ofctl_controller.add_flow(flow.get_flow())

        for flow in fgd.arp_flows:
            fgd.nfvi_pop.edge_controller.add_arp_reply(flow.get_flow())

    return fgds


def del_chain(fgds):
    for fgd in fgds:
        for flow in fgd.arp_flows:
            fgd.nfvi_pop.edge_controller.del_arp_reply(flow.get_flow())

        for hop in fgd.hops:
            for flow in hop.flows:
                print(flow.get_flow())
                print(fgd.nfvi_pop.ofctl_controller.del_flow(flow.get_flow()))


def get_all_switches(cloud):
    all_switches = cloud.topology_controller.get_switches()

    switches = []
    if all_switches is not None:
        for switch in all_switches:
            sw = cloud.core_controller.get_switches(dpid=switch['dpid'])
            if sw is not None:
                switches.append(Switch(**sw))
                switches[-1].set_ports(switch['ports'])
            else:
                switches.append(Switch(**switch))

    return switches


def get_edge_switches(cloud):
    edge_switches = cloud.edge_controller.get_switches()

    switches = []
    if edge_switches is not None:
        for edge_switch in edge_switches:
            sw = cloud.topology_controller.get_switches(
                dpid=edge_switch['dpid'])[0]
            switches.append(Switch(**sw))

    return switches


def get_core_switches(cloud):
    core_switches = cloud.core_controller.get_switches()

    switches = []
    if core_switches is not None:
        for core_switch in core_switches:
            sw = cloud.topology_controller.get_switches(core_switch['dpid'])[0]
            switches.append(Switch(**sw))
            switches[-1].key = core_switch['key']

    return switches


def get_gateway_switches(cloud):
    gateway_switches = cloud.gateway_controller.get_switches()

    switches = []
    if gateway_switches is not None:
        for gateway_switch in gateway_switches:
            sw = cloud.topology_controller.get_switches(
                gateway_switch['dpid'])[0]
            switches.append(Switch(**sw))

    return switches


def get_all_links(cloud):
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


def create_domain_graph(cloud):
    switches = get_all_switches(cloud)
    links = get_all_links(cloud)
    graph = GraphUndirectedWeighted(switches)

    for link in links:
        graph.add_edge(link.port_src.dpid, link.port_dst.dpid, 1)

    return graph


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

        return shortest_path
