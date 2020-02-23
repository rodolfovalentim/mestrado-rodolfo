import json
import logging
from operator import attrgetter

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                    set_ev_cls)
from ryu.lib import mac as mac_lib
from ryu.lib.packet import arp, ether_types, ethernet, icmp, ipv4, packet
from ryu.ofproto import (ether, inet, ofproto_v1_0, ofproto_v1_2, ofproto_v1_3,
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
        self.hw_addr = "DE:AD:C0:DE:CA:FE"
        self.ip_addr = '10.0.0.254'
        self.ip_to_dpid = {}

    # This method add a flow to send every packet to controller
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch(eth_dst=("DE:AD:C0:DE:CA:FE"))
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 100, match, actions)

    # It need a method to receive a packet in using of keyflow and add a flow to process
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        port = msg.match['in_port']
        pkt = packet.Packet(data=msg.data)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self.logger.info("packet-in %s" % (pkt,))
            self.logger.info('The IP {} is connected to switch {}'.format(
                pkt_arp.src_ip, hex(datapath.id)[2:].zfill(16)))
            self.ip_to_dpid[pkt_arp.src_ip] = hex(datapath.id)[2:].zfill(16)
            return

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)
        return

    def _send_arp(self, datapath, ip):
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=ether.ETH_TYPE_ARP,
                                           dst=mac_lib.BROADCAST_STR,
                                           src=self.hw_addr))

        pkt.add_protocol(arp.arp(opcode=arp.ARP_REQUEST,
                                 src_mac=self.hw_addr,
                                 proto=ether.ETH_TYPE_IP,
                                 src_ip=self.ip_addr,
                                 dst_mac=mac_lib.DONTCARE_STR,
                                 dst_ip=ip))

        self._flood_packet(datapath, pkt)

    def _flood_packet(self, datapath, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

    def host_discovery(self, ip):
        switches = get_switch(self, None)
        for switch in switches:
            self._send_arp(switch.dp, ip)


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
        datapath = None
        switches = get_switch(self.edge_app, None)
        for switch in switches:
            if str(switch.dp.id) == req.json.get('dpid'):
                datapath = switch.dp
                self._del_arp_reply_flow(datapath,
                     in_port=req.json.get('in_port'),
                     arp_tpa=req.json.get('arp_tpa'))

    def _add_arp_reply_flow(self, datapath, in_port, arp_tpa, arp_tha):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
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

      
    def _del_arp_reply_flow(self, datapath, in_port, arp_tpa):
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            in_port=int(in_port),
            eth_type=ether_types.ETH_TYPE_ARP,
            arp_op=arp.ARP_REQUEST,
            arp_tpa=arp_tpa)

        self._del_flow(datapath, PRIORITY_ARP_REPLY, match)

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

        print(match)

        datapath.send_msg(mod)

    # Example of a request to add and delete an arp reply flow
    # {
    # 	"dpid": "1",
    # 	"in_port": "1",
    # 	"arp_tpa": "10.0.0.2",
    # 	"arp_tha": "90:01:02:AB:03:02"
    # }

    @route('discovery', '/discovery/{ip}', methods=['GET'])
    def discovery(self, req, ip, **kwargs):
        self.edge_app.host_discovery(ip)
        return Response(content_type='application/json', json={}, status=200)

    @route('get', '/ip2dp/{ip}', methods=['GET'])
    def get_ip(self, req, ip, **kwargs):
        dpid = self.edge_app.ip_to_dpid.get(ip, None)
        if dpid is not None:
            body = {'ip': ip, 'dpid': dpid}
            return Response(content_type='application/json', json=body, status=200)

        return Response(content_type='application/json', json={}, status=404)

    @route('nodes', '/switches', methods=['GET'])
    def get_nodes(self, req, **kwargs):
        switches = get_switch(self.edge_app, None)
        body = [{'dpid': hex(switch.dp.id)[2:].zfill(16), 
                 'ip': switch.dp.socket.getpeername()[0]
                 } for switch in switches]
        return Response(content_type='application/json', json=body)