import json
import logging

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                    set_ev_cls)
from ryu.lib.packet import arp, ethernet, icmp, ipv4, packet
from ryu.ofproto import (ofproto_v1_0, ofproto_v1_2, ofproto_v1_3,
                         ofproto_v1_4, ofproto_v1_5)
from ryu.topology.api import get_switch
from webob import Response

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

edge_instance_name = 'edge_api_app'


class EdgeController(app_manager.RyuApp):

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION,
                    ofproto_v1_4.OFP_VERSION,
                    ofproto_v1_5.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(EdgeController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(RestController, {edge_instance_name: self})


class RestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RestController, self).__init__(req, link, data, **config)
        self.edge_app = data[edge_instance_name]

    @route('nodes', '/switches', methods=['GET'])
    def get_nodes(self, req, **kwargs):
        switches = get_switch(self.edge_app, None)
        body = [{'dpid': hex(switch.dp.id)[2:].zfill(16), 
                 'ip': switch.dp.socket.getpeername()[0]
                 } for switch in switches]
        return Response(content_type='application/json', json=body)