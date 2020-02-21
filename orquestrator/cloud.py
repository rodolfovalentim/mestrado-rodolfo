import logging
import daiquiri
import openstack
from openstack.config import loader

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)

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

    def get_port(self):
        return self.taps[0].name


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

    def get_ip(self):
        return self.ip

class Cloud(object):
    def __init__(self, name):
        self.name = name

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

    def get_name(self):
        return self.name

    def get_all_virtual_machines(self):
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

    def create_virtual_machine(self, name, image, flavor, network, availability_zone, may_exist=False):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud=self.name)

        server = self.find_virtual_machine(name)
        logger.info(server)
        if server is not None:
            if may_exist:
                return server
            else:
                return

        image = conn.compute.find_image(image)
        flavor = conn.compute.find_flavor(flavor)
        network = conn.network.find_network(network)

        server = conn.compute.create_server(
            name=name, image_id=image.id, flavor_id=flavor.id,
            availability_zone=availability_zone,
            networks=[{"uuid": network.id}])

        server = conn.compute.wait_for_server(server)

        return VirtualMachine(**server)

    def find_virtual_machine(self, name):
        config = loader.OpenStackConfig()
        conn = openstack.connect(cloud=self.name)
        server = conn.compute.find_server(name)

        if server:
            vm = VirtualMachine(**server)
            for port in conn.network.ports():
                if(port.get('device_id') == vm.uuid):
                    vm.add_tap(Tap(**port))
            return vm
        return None
    
    def get_gateway(self):
        return self.gateway_controller.get_switches()[0]
