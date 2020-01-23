from prettyprinter import pprint

from cloud import Cloud
from controller import (CoreController, EdgeController,
                    ExternalController, TopologyController, GatewayController)

import orquestrator as orq
import daiquiri
import logging

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)

if __name__ == "__main__":
    
    topo_ctrl_n1 = TopologyController(endpoint="127.0.0.1", port="6634", wsgi_port="8080")
    core_ctrl_n1 = CoreController(endpoint="127.0.0.1", port="6635", wsgi_port="8081")
    edge_ctrl_n1 = EdgeController(endpoint="127.0.0.1", port="6636", wsgi_port="8082")
    ext_ctrl_n1 = ExternalController(endpoint="127.0.0.1", port="6637", wsgi_port="8083")
    gw_ctrl_n1 = GatewayController(endpoint="127.0.0.1", port="6638", wsgi_port="8084")
    
    topo_ctrl_n2 = TopologyController(endpoint="127.0.0.1", port="6634", wsgi_port="8080")
    core_ctrl_n2 = CoreController(endpoint="127.0.0.1", port="6635", wsgi_port="8081")
    edge_ctrl_n2 = EdgeController(endpoint="127.0.0.1", port="6636", wsgi_port="8082")
    ext_ctrl_n2 = ExternalController(endpoint="127.0.0.1", port="6637", wsgi_port="8083")
    gw_ctrl_n2 = GatewayController(endpoint="127.0.0.1", port="6638", wsgi_port="8084")
    
    cloud1 = Cloud(name='nuvem01')
    cloud1.set_topology_controller(topo_ctrl_n1)
    cloud1.set_core_controller(core_ctrl_n1)
    cloud1.set_edge_controller(edge_ctrl_n1)
    cloud1.set_external_controller(ext_ctrl_n1)
    cloud1.set_gateway_controller(gw_ctrl_n1)
    
    cloud2 = Cloud(name='nuvem02')
    cloud2.set_topology_controller(topo_ctrl_n2)
    cloud2.set_core_controller(core_ctrl_n2)
    cloud2.set_edge_controller(edge_ctrl_n2)
    cloud2.set_external_controller(ext_ctrl_n2)
    cloud2.set_gateway_controller(gw_ctrl_n2)
    

    dpi = orq.create_virtual_function(cloud=cloud1,
                                      name='dpi', 
                                      availability_zone='nova:controller', 
                                      vnf_type="dpi",
                                      may_exist=True)
    
    nat = orq.create_virtual_function(cloud=cloud1,
                                    name='nat',
                                    availability_zone='nova:compute01', 
                                    vnf_type="nat",
                                    may_exist=True)

    
    edge_fw1 = orq.create_virtual_function(cloud=cloud1,
                                      name='edge_firewall_1',
                                      availability_zone='nova:compute01', 
                                      vnf_type="edge_firewall_1",
                                      may_exist=True)

    edge_fw2 = orq.create_virtual_function(cloud=cloud2,
                                      name='edge_firewall_2', 
                                      availability_zone='nova:controller', 
                                      vnf_type="edge_firewall_2",
                                      may_exist=True)    
    
    dst = orq.create_virtual_function(cloud=cloud2,
                                      name='dst', 
                                      availability_zone='nova:controller', 
                                      vnf_type="dst",
                                      may_exist=True)
    
    
    # orq.create_chain(classifier={
    #     'source_ip': '10.0.0.1',
    #     'source_port': 80,
    #     'source_cloud': cloud1,
    #     'destination_ip': '10.0.101.15',
    #     'destination_port': 80,
    #     'protocol': 'udp',
    #     'destination_cloud': cloud2
    # }, service_chain=[dpi, edge_fw1])

