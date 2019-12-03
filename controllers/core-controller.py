import re
from ryu.base import app_manager
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

core_instance_name = 'core_api_app'

class CoreController(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }
    
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION,
                    ofproto_v1_4.OFP_VERSION,
                    ofproto_v1_5.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(CoreController, self).__init__(*args, **kwargs)
        self.logger.info("Init of Core Controller...")
        self.pool = [19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73]
        self.dpid_to_key = {}
        self.mac_to_port = {}
        wsgi = kwargs['wsgi']
        wsgi.register(RestController, {core_instance_name: self})

    # This method add a flow to send every packet to controller
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if self.dpid_to_key.get(datapath.id):
            return

        new_key = self.pool.pop()
        if not new_key:
            return

        # install the table-miss flow entry.
        match = parser.OFPMatch(
            eth_src=("00:00:00:00:00:00", "00:00:00:00:00:00"))
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.logger.info("Switch %s has key %s" % (datapath.id, new_key))
        self.dpid_to_key[datapath.id] = new_key
        self.add_flow(datapath, 0, match, actions)

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

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
        pkt_keyflow = pkt.get_protocol(ethernet.ethernet)
        if pkt_keyflow.src[0:2] == '90':
            self._handle_keyflow(datapath, port, pkt_keyflow, pkt)
            return
        elif pkt_keyflow.dst == '01:80:c2:00:00:0e':
            return
        else:
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            # get Datapath ID to identify OpenFlow switches.
            dpid = datapath.id
            self.mac_to_port.setdefault(dpid, {})

            # analyse the received packets using the packet library.
            pkt = packet.Packet(msg.data)
            eth_pkt = pkt.get_protocol(ethernet.ethernet)
            dst = eth_pkt.dst
            src = eth_pkt.src

            # get the received port number from packet_in message.
            in_port = msg.match['in_port']

            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

            # learn a mac address to avoid FLOOD next time.
            self.mac_to_port[dpid][src] = in_port

            # if the destination mac address is already learned,
            # decide which port to output the packet, otherwise FLOOD.
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD

            # construct action list.
            actions = [parser.OFPActionOutput(out_port)]

            # install a flow to avoid packet_in next time.
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                self.add_flow(datapath, 1, match, actions)

            # construct packet_out message and send it.
            out = parser.OFPPacketOut(datapath=datapath,
                                    buffer_id=ofproto.OFP_NO_BUFFER,
                                    in_port=in_port, actions=actions,
                                    data=msg.data)
            datapath.send_msg(out)

    def _handle_keyflow(self, datapath, port, pkt_keyflow, pkt):
        # self.logger.info("packet-in %s" % (pkt,))
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch(
            in_port=port, eth_src=(pkt_keyflow.src))

        route_key = self.mac_to_int(pkt_keyflow.src[0:11])
        switch_key = self.dpid_to_key[datapath.id]
        output_port = route_key % switch_key

        self.logger.info("Inserting flow packets from %s with key %s output to %s" % (
            datapath.id, switch_key, output_port,))

        actions = [parser.OFPActionOutput(
            output_port, ofproto.OFPCML_NO_BUFFER)]
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

    def mac_to_int(self, mac):
        res = re.match(
            '^((?:(?:[0-9a-f]{2}):){3}[0-9a-f]{2})$', mac.lower())
        if res is None:
            raise ValueError('invalid mac address')
        return int(res.group(0).replace(':', ''), 16)


class RestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RestController, self).__init__(req, link, data, **config)
        self.core_app = data[core_instance_name]

    @route('nodes', '/switches', methods=['GET'])
    def get_nodes(self, req, **kwargs):
        return self._switches()

    @route('nodes', '/switch/{dpid}', methods=['GET'])
    def get_switch(self, req, dpid, **kwargs):
        body = {}
        for switch in get_switch(self.core_app, None):
            if hex(switch.dp.id)[2:].zfill(16) == dpid:
                body = {'dpid': hex(switch.dp.id)[2:].zfill(16), 
                'ip': switch.dp.socket.getpeername()[0], 
                'key': self.core_app.dpid_to_key.get(switch.dp.id)}
                return Response(content_type='application/json', json=body)
        return Response("Not found", 404)

    
        
    def _switches(self):
        dpid = None
        switches = get_switch(self.core_app, dpid)
        body = [{'dpid': hex(switch.dp.id)[2:].zfill(16), 
                'ip': switch.dp.socket.getpeername()[0], 
                'key': self.core_app.dpid_to_key.get(switch.dp.id)} for switch in switches]
        
        print(body)

        return Response(content_type='application/json', json=body)