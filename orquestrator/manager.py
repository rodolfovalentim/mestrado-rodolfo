from prettyprinter import pprint

from orquestrator import (Cloud, CoreController, EdgeController,
                          ExternalController, Orquestrator, TopologyController)

if __name__ == "__main__":

    topo_ctrl = TopologyController(
        endpoint="127.0.0.1", port="6634", wsgi_port="8080")
    core_ctrl = CoreController(
        endpoint="127.0.0.1", port="6635", wsgi_port="8081")
    edge_ctrl = EdgeController(
        endpoint="127.0.0.1", port="6636", wsgi_port="8082")
    ext_ctrl = ExternalController(
        endpoint="127.0.0.1", port="6637", wsgi_port="8083")

    cloud = Cloud()
    cloud.set_topology_controller(topo_ctrl)
    cloud.set_core_controller(core_ctrl)
    cloud.set_edge_controller(edge_ctrl)
    cloud.set_external_controller(ext_ctrl)

    orq = Orquestrator()
    orq.cloud = cloud

    classifier = {
                    'source_ip': '10.0.0.1',
                    'source_port': 80,
                    'destination_ip': '10.0.101.15',
                    'destination_port': 80,
                    'protocol': 'udp',
                }

    flow_classifier = orq.create_flow_classifier(cloud='nuvem02', 
                                                 flow_classifier=classifier)

    # nat = orq.create_virtual_function(
    #     name='src', compute_host='compute01', vnf_type="nat", cloud='nuvem01')

    # gw_sfc_n1 = orq.get_gateway(cloud='nuvem01')

    # gw_sfc_n2 = orq.get_gateway(cloud='nuvem02')

    # dpi = orq.create_virtual_function(
    #     name='src', compute_host='controller', vnf_type="dpi", cloud='nuvem02')

    # orq.create_chain(flow_classifier=flow_classifier, service_chain=[nat, gw_sfc_n1,
    #                         gw_sfc_n2, dpi], simetric=False)
