import json
import logging
from operator import attrgetter

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.lib import mac as mac_lib
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                    set_ev_cls)
from ryu.lib.packet import arp, ethernet, icmp, ipv4, packet
from ryu.ofproto import (ether, inet, ofproto_v1_0, ofproto_v1_2, ofproto_v1_3,
                         ofproto_v1_4, ofproto_v1_5)
from ryu.topology.api import get_switch
from webob import Response
from ryu.ofproto.ofproto_v1_5_parser import OFPActionSetField

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

LOG = logging.getLogger('SimpleArp')
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

gateway_instance_name = 'gateway_api_app'
PRIORITY_FLOW_REPLY = 101
TABLE_ID_EGRESS = 0
TABLE_ID_INGRESS = 0 


class TunnelController(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION,
                    ofproto_v1_4.OFP_VERSION,
                    ofproto_v1_5.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TunnelController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(RestController, {gateway_instance_name: self})

class RestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RestController, self).__init__(req, link, data, **config)
        self.gateway_app = data[gateway_instance_name]

    @route('nodes', '/switches', methods=['GET'])
    def get_nodes(self, req, **kwargs):
        switches = get_switch(self.gateway_app, None)
        body = [{'dpid': hex(switch.dp.id)[2:].zfill(16), 
                 'ip': switch.dp.socket.getpeername()[0]
                 } for switch in switches]
        return Response(content_type='application/json', json=body)

    @route('nodes', '/stats/flowentry/add', methods=['POST'])
    def add_flow(self, req, **kwargs):
        datapath = None
        switches = get_switch(self.gateway_app, None)
        for switch in switches:
            print(switch.dp.id, req.json.get('dpid'))
            if str(switch.dp.id) == str(req.json.get('dpid')):
                print(switch.dp)
                datapath = switch.dp
                if len(req.json.get('actions')) > 1:
                    self._add_output_flow(datapath, match=req.json.get('match'), new_eth_dst=req.json.get('actions')[0].get('value'), out_port=req.json.get('actions')[-1].get('port'))
                else: 
                    self._add_output_flow(datapath, match=req.json.get('match'), out_port=req.json.get('actions')[-1].get('port'))
                    

    @route('nodes', '/stats/flowentry/delete_strict', methods=['POST'])
    def del_flow(self, req, **kwargs):
        datapath = None
        switches = get_switch(self.gateway_app, None)
        for switch in switches:
            if str(switch.dp.id) == str(req.json.get('dpid')):
                datapath = switch.dp
                self._del_output_flow(datapath, match=req.json.get('match'))

    def _add_output_flow(self, datapath, match, out_port, new_eth_dst=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(**match)

        actions = []
        if new_eth_dst is not None:
            actions += [parser.OFPActionSetField(eth_dst=new_eth_dst)]
            
        actions += [parser.OFPActionOutput(int(out_port))]
    
        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]

        self._add_flow(datapath, PRIORITY_FLOW_REPLY, match, instructions)

      
    def _del_output_flow(self, datapath, match):
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(**match)

        self._del_flow(datapath, PRIORITY_FLOW_REPLY, match)

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
