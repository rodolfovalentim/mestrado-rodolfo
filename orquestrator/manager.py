from orquestrator import (TopologyController, CoreController, EdgeController, Cloud, Orquestrator)
from prettyprinter import pprint

if __name__ == "__main__":

    topo_ctrl = TopologyController(endpoint="127.0.0.1", port="6634", wsgi_port="8080")
    core_ctrl = CoreController(endpoint="127.0.0.1", port="6635", wsgi_port="8081")
    edge_ctrl = EdgeController(endpoint="127.0.0.1", port="6636", wsgi_port="8082")

    cloud = Cloud()
    cloud.set_topology_controller(topo_ctrl)
    cloud.set_core_controller(core_ctrl)
    cloud.set_edge_controller(edge_ctrl)
    
    pprint(cloud.get_switches())
    pprint(cloud.get_links())
    pprint(cloud.get_virtual_machines())

    orq = Orquestrator()
    orq.cloud = cloud
    orq.get_graph()
    pprint(orq.graph)
    # path = orq.get_hop_path('0000000000000002', "0000000000000007")
    # print(path)