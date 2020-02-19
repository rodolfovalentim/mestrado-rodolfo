import json
import logging

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                    set_ev_cls)
from ryu.lib.packet import arp, ether_types, ethernet, icmp, ipv4, packet
from ryu.ofproto import (ofproto_v1_0, ofproto_v1_2, ofproto_v1_3,
                         ofproto_v1_4, ofproto_v1_5)
from ryu.topology.api import get_switch
from webob import Response

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

edge_instance_name = 'edge_api_app'

PRIORITY_ARP_REPLY = 101
TABLE_ID_EGRESS = 0
TABLE_ID_INGRESS = 0

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

    @route('nodes', '/add_arp_flow', methods=['POST'])
    def add_arp_flow(self, req, **kwargs):
        datapath = None
        switches = get_switch(self.edge_app, None)
        for switch in switches:
            if str(switch.dp.id) == req.json.get('dpid'):
                datapath = switch.dp
                self._add_arp_reply_flow(datapath, in_port=req.json.get('in_port'),
                     arp_tpa=req.json.get('arp_tpa'), arp_tha=req.json.get('arp_tha'))
                

    @route('nodes', '/del_arp_flow', methods=['POST'])
    def del_arp_flow(self, req, **kwargs):
        pass

    def _add_arp_reply_flow(self, datapath, in_port, arp_tpa, arp_tha):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            # metadata=(tag, parser.UINT64_MAX),    
            in_port=int(in_port),
            eth_type=ether_types.ETH_TYPE_ARP,
            arp_op=arp.ARP_REQUEST,
            arp_tpa=arp_tpa)

        actions = [
            parser.NXActionRegMove(
                src_field="eth_src", dst_field="eth_dst", n_bits=48),
            parser.OFPActionSetField(eth_src=arp_tha),
            parser.OFPActionSetField(arp_op=arp.ARP_REPLY),
            parser.NXActionRegMove(
                src_field="arp_sha", dst_field="arp_tha", n_bits=48),
            parser.NXActionRegMove(
                src_field="arp_spa", dst_field="arp_tpa", n_bits=32),
            parser.OFPActionSetField(arp_sha=arp_tha),
            parser.OFPActionSetField(arp_spa=arp_tpa),
            parser.OFPActionOutput(ofproto.OFPP_IN_PORT)]
        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]

        self._add_flow(datapath, PRIORITY_ARP_REPLY, match, instructions,
                       table_id=TABLE_ID_EGRESS)

    @staticmethod
    def _add_flow(datapath, priority, match, instructions,
                table_id=TABLE_ID_INGRESS):
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=table_id,
            priority=priority,
            match=match,
            instructions=instructions)

        datapath.send_msg(mod)

    @staticmethod
    def _del_flow(datapath, priority, match, table_id=TABLE_ID_INGRESS):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=table_id,
            command=ofproto.OFPFC_DELETE,
            priority=priority,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=match)

        datapath.send_msg(mod)

# Example of a request
# {
# 	"dpid": "1",
# 	"in_port": "1",
# 	"arp_tpa": "10.0.0.2",
# 	"arp_tha": "90:01:02:AB:03:02"
# }