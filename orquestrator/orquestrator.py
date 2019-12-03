import json
import queue
import requests
from collections import namedtuple
from functools import reduce
import openstack
from openstack.config import loader
import sys
from prettyprinter import pprint

# openstack.enable_logging(True, stream=sys.stdout)
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
        if b == 1: return 1
        while a > 1:
            q = a // b
            a, b = b, a % b
            x0, x1 = x1 - q * x0, x0
        if x1 < 0:
            x1 += b0
        return x1

# print(chinese_remainder([11, 19], [7, 5]), hex(chinese_remainder([11, 19], [7, 5])))

class Tap(object):
    def __init__(self, *args, **kwargs):
        self.uuid = kwargs.get('id', None)
        self.mac_address = kwargs.get('mac_address', None)
        self.name = "qvo" + kwargs.get('id', None)[0:11]
        fixed_ips = kwargs.get('fixed_ips', None)
        if fixed_ips is not None and len(fixed_ips) > 0:
            self.ip = fixed_ips[0].get("ip_address")

    def __repr__(self):
        return 'Tap {}'.format(self.__dict__)

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
        # self.controller = kwargs.get('controller', None)
        self.dpid = kwargs.get('dpid', None)
        self.ports = [ Port(**port) for port in kwargs.get('ports') ]
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

    def set_controller(self, controller):
        self.controller = controller

class Flow(object):

    match = {}
    actions = []

    def add_match_field(self, field, value):
        self.match[field] = value

    def add_action(self, action):
        self.actions.append(action)

    def get_flow(self):
        return { 'match': self.match, "actions": self.actions }

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
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()

        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
            return        

        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
            return        

        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
            return        

        except KeyboardInterrupt:
            print("Someone closed the program")
            return        

        r_switches = response.json()
        return r_switches

    def get_links(self):    
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.links_path)
        response = None
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
            return        
        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
            return        
        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
            return        

        except KeyboardInterrupt:
            print("Someone closed the program")
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
        url = "http://{}:{}/{}/{}".format(self.endpoint, self.wsgi_port, self.switch_path, dpid)

        try: 
            response = requests.get(url)
            response.raise_for_status()
        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
            return        

        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
            return        

        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
            return        

        except KeyboardInterrupt:
            print("Someone closed the program")
            return        

        r_switches = response.json()
        return r_switches

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.switches_path)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
            return        

        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
            return        

        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
            return        

        except KeyboardInterrupt:
            print("Someone closed the program")
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
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.add_flow_path)
        return requests.post(url, json=flow)
        
    def del_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.del_flow_path)
        return requests.post(url, json=flow)

    def mod_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.mod_flow_path)
        return requests.post(url, json=flow)

    def get_switches(self):
        url = "http://{}:{}/{}".format(self.endpoint, self.wsgi_port, self.switches_path)

        try: 
            response = requests.get(url)
            response.raise_for_status()
        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
            return []

        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
            return []     

        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
            return []   

        except KeyboardInterrupt:
            print("Someone closed the program")
            return []     

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

    topology_controller = None
    edge_controller = None
    core_controller = None

    def set_topology_controller(self, controlller):
        self.topology_controller = controlller
    
    def set_edge_controller(self, controller):
        self.edge_controller = controller

    def set_core_controller(self, controller):
        self.core_controller = controller
  
    def get_switches(self):
        all_switches = self.topology_controller.get_switches()
                
        if(all_switches is None):
            print("Some Error occur during topology discovery. Check controllers and network")
            return 

        r_core_switches = [switch.get('dpid') for switch in self.core_controller.get_switches()]
        r_edge_switches = [switch.get('dpid') for switch in self.edge_controller.get_switches()]
        
        if(r_core_switches is None or r_edge_switches is None):
            print("Some Error occur during core and edge discovery. Check controllers and network")
            return 

        switches = []
        
        for switch in all_switches:
            sw = Switch(**switch)
            if sw.dpid in r_core_switches:
                sw.switch_type = 'core'
                core_sw = self.core_controller.get_switch(sw.dpid)
                if core_sw:
                    sw.key = core_sw.get('key')
            elif sw.dpid in r_edge_switches:
                sw.switch_type = 'edge'
            else:
                sw.switch_type = 'default'
            switches.append(sw)
        
        return switches

    def get_links(self):
        r_links = self.topology_controller.get_links()

        links = []
        for link in r_links:
            links.append(Link(**link))
        
        return links

    def get_virtual_machines(self):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud="nuvem01")

        vms = []
        for server in conn.compute.servers():
            vm = VirtualMachine(**server)
            for port in conn.network.ports():
                if(port.get('device_id') == vm.uuid):
                    vm.add_tap(Tap(**port))
            vms.append(vm)
        return vms

class Orquestrator(object):

    def __init__(self):
        self.cloud = None 
        self.graph = None
        self.chains = None

    def add_chain(self, chain):
        hops = []
        for i in range(len(chain)):
            if (i + 1 < len(chain) - 1):
                hops.append((chain[i], chain[i+1]))

    def get_graph(self):
        self.graph = GraphUndirectedWeighted(self.cloud.switches)
            
        for link in self.cloud.links:
            self.graph.add_edge(link.port_src.dpid, link.port_dst.dpid, 1)

    def get_hop_path(self, edge_source, edge_destination):
        return self.graph.dijkstra(edge_source, edge_destination)
