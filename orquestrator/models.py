import json
import logging
import queue
import sys
from collections import namedtuple
from functools import reduce

import daiquiri
import openstack
import requests
from netaddr import IPNetwork
from openstack.config import loader
from prettyprinter import pprint
from requests_futures import sessions

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)
Edge = namedtuple('Edge', ['vertex', 'weight'])


class KeyFlowAgent(object):

    @staticmethod
    def chinese_remainder(n, a):
        """ Calcula a chave key flow.
        entrada:
        n: lista ordenada do ids dos swiches
        a: lista ordenada das portas em que vai sair
        saida:
        chave com numeros inteiros do caminho
        """
        sum = 0
        prod = reduce(lambda a, b: a * b, n)

        for n_i, a_i in zip(n, a):
            p = prod // n_i
            sum += a_i * KeyFlowAgent.mul_inv(p, n_i) * p
        return sum % prod

    @staticmethod
    def mul_inv(a, b):
        b0 = b
        x0 = 0
        x1 = 1
        if b == 1:
            return 1
        while a > 1:
            q = a // b
            a, b = b, a % b
            x0, x1 = x1 - q * x0, x0
        if x1 < 0:
            x1 += b0
        return x1

# print(chinese_remainder([11, 19], [7, 5]), hex(chinese_remainder([11, 19], [7, 5])))

class VirtualMachine(object):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', None)
        self.uuid = kwargs.get('id', None)
        self.host_id = kwargs.get('compute_host', None)
        self.taps = []

    def __repr__(self):
        return 'Virtual Machine {}'.format(self.__dict__)

    def add_tap(self, tap):
        self.taps.append(tap)

class VirtualNetworkFunction(VirtualMachine):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', None)
        self.uuid = kwargs.get('id', None)
        self.host_id = kwargs.get('compute_host', None)
        self.taps = []
        self.nf_type = kwargs.get('nf_type', None)
        self.cloud = kwargs.get('cloud', None)

    def __repr__(self):
        return 'Virtual Machine {}'.format(self.__dict__)

    def get_cloud(self):
        return self.cloud            

    def add_tap(self, tap):
        self.taps.append(tap)

class Tap(object):
    def __init__(self, *args, **kwargs):
        self.uuid = kwargs.get('id', None)
        self.mac_address = kwargs.get('mac_address', None)
        self.name = "qvo" + kwargs.get('id', None)[0:11]
        self.binded_host = kwargs.get('binding_host_id', None)

        fixed_ips = kwargs.get('fixed_ips', None)
        if fixed_ips is not None and len(fixed_ips) > 0:
            self.ip = fixed_ips[0].get("ip_address")

    def __repr__(self):
        return 'Tap {}'.format(self.__dict__)


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

    def get_output_port_no(self):
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
        self.match = {}
        self.actions = []

    def __repr__(self):
        return 'Switch {}'.format(self.__dict__)

    def get_flow(self):
        return {'match': self.match, "actions": self.actions}

    def to_dict(self):
        return {
            "dpid": self.switch.dpid,
            "table": 0,
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


class FlowClassifier(object):
    def __init__(self, *args, **kwargs):
        self.switch: Switch = kwargs.get('switch', None)
        self.flow: Flow = kwargs.get('flow', {})


class Controller(object):
    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.get('endpoint', '127.0.0.1')
        self.port = kwargs.get('port', '6633')


class TopologyController(Controller):
    switches_path = "v1.0/topology/switches"
    links_path = "v1.0/topology/links"

    def __init__(self, *args, **kwargs):
        super().__init__(kwargs)
        self.wsgi_port = kwargs.get('wsgi_port', '8080')

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_switches = response.json()
        return r_switches

    def get_links(self):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.links_path)
        response = None
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_links = response.json()
        return r_links


class CoreController(Controller):
    switches_path = 'switches'
    switch_path = 'switch'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port', '8080')

    def get_keys(self):
        pass

    def get_switch(self, dpid):
        url = "http://{}:{}/{}/{}".format(self.endpoint,
                                          self.wsgi_port, self.switch_path, dpid)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_switches = response.json()
        return r_switches

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_switches = response.json()
        return r_switches


class ExternalController(Controller):
    discovery_path = 'discovery'
    ip2dp_path = 'ip2dp'
    switches_path = 'switches'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port', '8080')

    def get_keys(self):
        pass

    def discover_subrede(self, ip_addr, mask):
        network = IPNetwork('/'.join([ip_addr, mask]))
        generator = network.iter_hosts()
        session = sessions.FuturesSession()

        futures = [
            session.get("http://{}:{}/{}/{}".format(self.endpoint,
                                                    self.wsgi_port,
                                                    self.discovery_path,
                                                    ip))
            for ip in list(generator)
        ]

        return

    def get_datapath_id(self, ip):
        url = "http://{}:{}/{}/{}".format(self.endpoint,
                                          self.wsgi_port,
                                          self.ip2dp_path,
                                          ip)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        switch_data = response.json()
        return switch_data

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_switches = response.json()
        return r_switches


class EdgeController(Controller):

    add_flow_path = 'stats/flowentry/add'
    del_flow_path = 'stats/flowentry/delete_strict'
    mod_flow_path = 'stats/flowentry/modify_strict'
    switches_path = 'switches'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port')

    def add_flow(self, switch, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.add_flow_path)
        return requests.post(url, json=flow)

    def del_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.del_flow_path)
        return requests.post(url, json=flow)

    def mod_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.mod_flow_path)
        return requests.post(url, json=flow)

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_switches = response.json()
        return r_switches
    
class GatewayController(Controller):
    
    add_flow_path = 'stats/flowentry/add'
    del_flow_path = 'stats/flowentry/delete_strict'
    mod_flow_path = 'stats/flowentry/modify_strict'
    switches_path = 'switches'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port')

    def add_flow(self, switch, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.add_flow_path)
        return requests.post(url, json=flow)

    def del_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.del_flow_path)
        return requests.post(url, json=flow)

    def mod_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.mod_flow_path)
        return requests.post(url, json=flow)

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return

        r_switches = response.json()
        return r_switches


class GraphUndirectedWeighted(object):
    def __init__(self, switches):
        self.switches = switches
        self.switches_count = len(switches)
        self.adjacency_list = [[] for _ in range(len(switches))]

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

    def dijkstra(self, source_dpid, dest_dpid):
        source = [x.get_dpid() for x in self.switches].index(source_dpid)
        dest = [x.get_dpid() for x in self.switches].index(dest_dpid)

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

class Cloud(object):
    def __init__(self, name):
        self.name = name
        self.topology_controller: TopologyController = None
        self.edge_controller: EdgeController = None
        self.core_controller: CoreController = None
        self.external_controller: ExternalController = None
        self.gateway_controller: GatewayController = None

    def set_topology_controller(self, controlller):
        self.topology_controller = controlller

    def set_edge_controller(self, controller):
        self.edge_controller = controller

    def set_core_controller(self, controller):
        self.core_controller = controller

    def set_external_controller(self, controller):
        self.external_controller = controller
        
    def set_gateway_controller(self, controller):
        self.gateway_controller = controller

    def get_switches(self):
        all_switches = self.topology_controller.get_switches()

        if(all_switches is None):
            logger.error(
                "Some Error occur during topology discovery. \
                    Check controllers and network")
            return

        d_switches = {}

        d_switches['edge'] = {
            switch['dpid']: switch for switch in self.edge_controller.get_switches()}
        
        d_switches['core'] = {
            switch['dpid']: switch for switch in self.core_controller.get_switches()}
        
        d_switches['external'] = {
            switch['dpid']: switch for switch in self.external_controller.get_switches()}

        assert d_switches['edge'] is not None
        assert d_switches['core'] is not None
        assert d_switches['external'] is not None

        switches = []

        for switch in all_switches:
            sw = Switch(**switch)

            if sw.dpid in d_switches['core'].keys():
                sw.switch_type = 'core'
                core_sw = self.core_controller.get_switch(sw.dpid)
                if core_sw:
                    sw.key = core_sw.get('key')
            elif sw.dpid in d_switches['edge'].keys():
                sw.switch_type = 'edge'
            elif sw.dpid in d_switches['external'].keys():
                sw.switch_type = 'external'

            switches.append(sw)

        return switches

    def get_links(self):
        r_links = self.topology_controller.get_links()

        links = []

        if r_links is None or len(r_links) < 0:
            return links

        for link in r_links:
            links.append(Link(**link))

        return links
    
    def get_gateway_switch(self):
        all_switches = self.topology_controller.get_switches()

        if(all_switches is None):
            logger.error(
                "Some Error occur during topology discovery. \
                    Check controllers and network")
            return

        d_switches = {switch['dpid']: switch for switch in self.gateway_controller.get_switches()}

        switch = None
        for switch in all_switches:
            sw = Switch(**switch)
            if sw.dpid in d_switches.keys():
                sw.switch_type = 'gateway'
                return switch
                
        assert switch is not None
        return  

    def get_virtual_machines(self):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud=self.name)

        vms = []
        for server in conn.compute.servers():
            vm = VirtualMachine(**server)
            for port in conn.network.ports():
                if(port.get('device_id') == vm.uuid):
                    vm.add_tap(Tap(**port))
            vms.append(vm)
        return vms

    def get_vm_ports(self):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud=self.name)
        ports = conn.network.ports()

        taps = []
        for port in ports:
            if port['device_owner'].startswith('compute'):
                taps.append(Tap(**port))

        return taps

    def create_virtual_machine(self, name, image, flavor, network, availability_zone):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud=self.name)

        logger.info("Create Server")
        image = conn.compute.find_image(image)
        flavor = conn.compute.find_flavor(flavor)
        network = conn.network.find_network(network)

        server = conn.compute.create_server(
            name=name, image_id=image.id, flavor_id=flavor.id,
            availability_zone=availability_zone,
            networks=[{"uuid": network.id}])

        server = conn.compute.wait_for_server(server)

        return server

    def find_virtual_machine(self, name):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud=self.name)
        server = conn.network.find_server(name)

        if server:
            return server
        return None



