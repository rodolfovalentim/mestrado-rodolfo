import argparse
import yaml


class Switch(object):
    self.host
    self.switch_type
    self.dpid
    self.ports
    self.flows


class EdgeController(object):
    self.endpoint
    self.port
    self.switches


class CoreController(object):
    self.endpoint
    self.port
    self.switches


class SFCGateway(object):
    self.endpoint
    self.port


class Cloud(object):
    self.endpoint
    self.user
    self.passwd
    self.region
    self.cloud_name
    self.edge_controller
    self.core_controller
    self.sfc_gateway


class FlowClassifier(object):
    self.description
    self.source_cloud
    self.source_ip
    self.source_port
    self.source_host
    self.source_tap
    self.destination_cloud
    self.destination_ip
    self.destination_port
    self.destination_host
    self.destination_tap
    self.protocol


class VirtualFunction(object):
    self.cloud
    self.host
    self.name
    self.description


class ForwardingGraph(object):
    self.graph
    self.description


class Chain(object):
    self.flow_classifier
    self.vnffg
    self.description


class Orquestrator(object):
    self.clouds
    self.chains

    def create_sfc(chain: Chain):
        # verify or create source and destination
        self.handle_flow_classifier(chain.flow_classifier)
        # create and verify vnfs info
        # get switches of core and edge in the chain
        core_switches, edge_switches = self.handle_vnffg(chain.vnffg)
        # get port topology
        topology = self.get_topology()
        # calculate chain key
        key = self.handle_routing(topology)
        # install flow in the edge switches in the chain
        return self.__create_sfc(edge_switches, key, chain.flow_classifier)

    def remove_sfc():
        # remove flows
        # remomve
        pass

    def update_sfc():
        pass

    def get_sfc():
        pass


if __name__ == "__main__":

    fc = FlowClassifier()
    fc.
