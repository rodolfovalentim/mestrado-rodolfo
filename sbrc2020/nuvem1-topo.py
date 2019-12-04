#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call


def myNetwork():

    net = Mininet(topo=None,
                  build=False,
                  ipBase='10.0.0.0/8')

    info('*** Adding controller\n')
    # Edge
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           protocol='tcp',
                           port=6636)

    # Core
    c1 = net.addController(name='c1',
                           controller=RemoteController,
                           protocol='tcp',
                           port=6635)

    # Topology
    c2 = net.addController(name='c2',
                           controller=RemoteController,
                           protocol='tcp',
                           port=6634)

    # External
    c3 = net.addController(name='c3',
                           controller=RemoteController,
                           protocol='tcp',
                           port=6637)

    info('*** Add switches\n')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch)
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info('*** Add hosts\n')
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
    h4 = net.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)

    info('*** Add links\n')
    net.addLink(h1, s7)
    net.addLink(h2, s6)
    net.addLink(h3, s1)
    net.addLink(h4, s2)
    net.addLink(s1, s3)
    net.addLink(s2, s4)
    net.addLink(s4, s5)
    net.addLink(s3, s5)
    net.addLink(s6, s5)
    net.addLink(s7, s5)

    info('*** Starting network\n')
    net.build()
    info('*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info('*** Starting switches\n')
    net.get('s1').start([c0, c2])
    net.get('s2').start([c0, c2])
    net.get('s3').start([c1, c2])
    net.get('s4').start([c1, c2])
    net.get('s5').start([c1, c2])
    net.get('s6').start([c0, c2, c3])
    net.get('s7').start([c0, c2, c3])

    info('*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    myNetwork()
