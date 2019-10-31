import re
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                    set_ev_cls)
from ryu.lib.packet import arp, ethernet, icmp, ipv4, packet
from ryu.ofproto import (ofproto_v1_0, ofproto_v1_2, ofproto_v1_3,
                         ofproto_v1_4, ofproto_v1_5)


class CoreController(app_manager.RyuApp):
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
            eth_src=("90:00:00:00:00:00", "ff:00:00:00:00:00"))
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
        self.logger.info("packet-in from %s" % (datapath.id))
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return
        pkt_keyflow = pkt.get_protocol(ethernet.ethernet)
        if pkt_keyflow:
            self._handle_keyflow(datapath, port, pkt_keyflow, pkt)
            return

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
