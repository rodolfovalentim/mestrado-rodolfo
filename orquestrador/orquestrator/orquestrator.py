import requests
from utils import (Switch, GraphUndirectedWeighted)

endpoint_core_controller = 'http://192.168.0.15'
topology_port = '8081'
switches_path = '/v1.0/topology/switches'
links_path = '/v1.0/topology/links'


class Orquestrator(object):

    switches_end = 'http://192.168.0.15:8081/v1.0/topology/switches'
    links_end = 'http://192.168.0.15:8081/v1.0/topology/links'

    switches = None
    link = None
    graph = None

    def get_topology(self):
        r_switches = requests.get(self.switches_end)
        r_links = requests.get(self.links_end)

        self.switches = []
        for switch in r_switches.json():
            self.switches.append(Switch(switch.get('dpid')))

        self.graph = GraphUndirectedWeighted(self.switches)

        for link in r_links.json():
            self.graph.add_edge(link.get('src').get('dpid'),
                                link.get('dst').get('dpid'), 1)

    def get_hop_path(self, edge_source, edge_destination, recheck=False):
        if recheck:
            self.get_topology()

        return self.graph.dijkstra(edge_source, edge_destination)


if __name__ == "__main__":

    orq = Orquestrator()
    orq.get_topology()
    orq.get_hop_path('0000000000000002', "0000000000000003")
