from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                    set_ev_cls)
from ryu.lib.packet import arp, ethernet, icmp, ipv4, packet
from ryu.ofproto import (ofproto_v1_0, ofproto_v1_2, ofproto_v1_3,
                         ofproto_v1_4, ofproto_v1_5)

import json
import logging

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_0
from ryu.topology.api import get_switch
from webob import Response


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

edge_instance_name = 'edge_api_app'

class KeyflowController(app_manager.RyuApp):

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION,
                    ofproto_v1_4.OFP_VERSION,
                    ofproto_v1_5.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(KeyflowController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(RestController, {edge_instance_name: self})

    # This method add a flow to send every packet to controller
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # It need a method to receive a packet in using of keyflow and add a flow to process
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        port = msg.match['in_port']
        pkt = packet.Packet(data=msg.data)
        # self.logger.info("packet-in %s" % (pkt,))
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self._handle_arp(datapath, port, pkt_ethernet, pkt_arp)
            return
        pkt_keyflow = pkt.get_protocol(ethernet.ethernet)
        if pkt_keyflow:
            self._handle_keyflow(datapath, port, pkt_keyflow, pkt)
            return

    def _handle_arp(self, datapath, port, pkt_ethernet, pkt_arp):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_ethernet.src,
                                           src=self.ip_to_ether[pkt_arp.dst_ip]))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=self.ip_to_ether[pkt_arp.dst_ip],
                                 src_ip=pkt_arp.dst_ip,
                                 dst_mac=pkt_arp.src_mac,
                                 dst_ip=pkt_arp.src_ip))
        self.logger.info("sending arp %s to %s" % (pkt, port, ))
        self._send_packet(datapath, port, pkt)

    def _handle_keyflow(self, datapath, port, pkt_keyflow, pkt):
        # self.logger.info("packet-in %s" % (pkt,))
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch(
            in_port=port, eth_dst=("aa:bb:cc:11:22:33", "00:00:00:00:ff:ff"))
        actions = [parser.OFPActionOutput(2 % 2, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
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

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)


class RestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RestController, self).__init__(req, link, data, **config)
        self.edge_app = data[edge_instance_name]

    @route('nodes', '/switches', methods=['GET'])
    def get_nodes(self, req, **kwargs):
        return self._switches()

    def _switches(self):
        dpid = None
        switches = get_switch(self.edge_app, dpid)
        body = [{'dpid': hex(switch.dp.id)[2:].zfill(16), 'ip': switch.dp.socket.getpeername()[0]} for switch in switches]
        print(body)
        return Response(content_type='application/json', json=body)