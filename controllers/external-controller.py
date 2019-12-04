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

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

LOG = logging.getLogger('SimpleArp')
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

external_instance_name = 'external_api_app'


class ExternalController(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION,
                    ofproto_v1_4.OFP_VERSION,
                    ofproto_v1_5.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExternalController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(RestController, {external_instance_name: self})
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
        self.logger.info("packet-in %s" % (pkt,))
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
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
        self.external_app = data[external_instance_name]

    @route('discovery', '/discovery/{ip}', methods=['GET'])
    def discovery(self, req, ip, **kwargs):
        self.external_app.host_discovery(ip)
        return Response(content_type='application/json', json={}, status=200)

    @route('get', '/ip2dp/{ip}', methods=['GET'])
    def get_ip(self, req, ip, **kwargs):
        dpid = self.external_app.ip_to_dpid[ip]
        if dpid is not None:
            body = {'ip': ip, 'dpid': dpid}
            return Response(content_type='application/json', json=body, status=200)

        return Response(content_type='application/json', json={}, status=404)