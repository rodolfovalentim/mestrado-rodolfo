import requests
import logging
import daiquiri
from netaddr.ip import IPNetwork
from requests import sessions

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)


class Controller(object):

    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.get('endpoint', '127.0.0.1')
        self.wsgi_port = kwargs.get('wsgi_port', '8080')
        self.port = kwargs.get('port', '6633')
        self.switches_path = 'switches'
        self.switch_path = 'switch'

    def get_switches(self, dpid=None):
        url = None

        if dpid is None:
            url = "http://{}:{}/{}".format(self.endpoint,
                                           self.wsgi_port, self.switches_path)
        else:
            url = "http://{}:{}/{}/{}".format(self.endpoint,
                                              self.wsgi_port, self.switch_path, dpid)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return None

        r_switches = response.json()
        return r_switches


class OFCTLController(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port')
        self.add_flow_path = 'stats/flowentry/add'
        self.del_flow_path = 'stats/flowentry/delete_strict'
        self.mod_flow_path = 'stats/flowentry/modify_strict'

    def add_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.add_flow_path)

        logger.info(url)
        logger.info(flow)

        return requests.post(url, json=flow)

    def del_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.del_flow_path)
        return requests.post(url, json=flow)

    def mod_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.mod_flow_path)
        return requests.post(url, json=flow)


class TopologyController(Controller):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port', '8080')
        self.switches_path = "v1.0/topology/switches"
        self.links_path = "v1.0/topology/links"

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
            return None

        r_links = response.json()
        return r_links

    def get_switches(self, dpid=None):
        url = None

        if dpid is None:
            url = "http://{}:{}/{}".format(self.endpoint,
                                           self.wsgi_port, self.switches_path)
        else:
            url = "http://{}:{}/{}/{}".format(self.endpoint,
                                              self.wsgi_port, self.switches_path, dpid)

            logger.debug(url)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return None

        r_switches = response.json()
        return r_switches


class CoreController(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EdgeController(Controller):
    discovery_path = 'discovery'
    ip2dp_path = 'ip2dp'
    switches_path = 'switches'
    add_arp_flow = 'add_arp_flow'
    del_arp_flow = 'del_arp_flow'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            return None

        switch_data = response.json()
        return switch_data

    def add_arp_reply(self, body):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port,
                                       self.add_arp_flow)

        try:
            response = requests.post(url, json=body)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return None

    def del_arp_reply(self, body):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port,
                                       self.del_arp_flow)

        try:
            response = requests.post(url, json=body)
            response.raise_for_status()
        except Exception as e:
            logger.error("Connection Error. Technical Details given below.")
            logger.error(str(e))
            return None


class GatewayController(Controller):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wsgi_port = kwargs.get('wsgi_port')
        self.add_flow_path = 'stats/flowentry/add'
        self.del_flow_path = 'stats/flowentry/delete_strict'

    def add_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.add_flow_path)

        logger.info(url)
        logger.info(flow)

        return requests.post(url, json=flow)

    def del_flow(self, flow):
        url = "http://{}:{}/{}".format(self.endpoint,
                                       self.wsgi_port, self.del_flow_path)

        logger.info(url)
        logger.info(flow)

        return requests.post(url, json=flow)
