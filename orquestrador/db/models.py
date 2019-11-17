from base import Base
from sqlalchemy import (Column, Index, Integer, BigInteger, Enum, String,
                        schema, Unicode)


class Switch(Base):
    """Represents a OpenvSwitch switch. Its flows, """
    __tablename__ = 'switches'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String(255), nullable=True)
    port = Column(String(255), nullable=True)
    flows = Column(String(300000), nullable=True)

    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        self.port = kwargs.get('port', None)
        self.flows = kwargs.get('flows', None)


class SFCGateway(Base):
    __tablename__ = 'sfc_gateways'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String(255), nullable=True)
    port = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        self.port = kwargs.get('port', None)


class EdgeController(Base):
    __tablename__ = 'edge_controllers'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String(255), nullable=True)
    port = Column(String(255), nullable=True)
    switches = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        self.port = kwargs.get('port', None)
        self.switches = kwargs.get('switches', None)


class Cloud(Base):
    __tablename__ = 'clouds'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String(255), nullable=True)
    user = Column(String(255), nullable=True)
    passwd = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True)
    cloud_name = Column(String(255), nullable=True)
    edge_controller = Column(String(255), nullable=True)
    core_controller = Column(String(255), nullable=True)
    sfc_gateway = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        self.user = kwargs.get('user', None)
        self.passwd = kwargs.get('passwd', None)
        self.region = kwargs.get('region', None)
        self.cloud_name = kwargs.get('cloud_name', None)
        self.edge_controller = kwargs.get('edge_controller', None)
        self.core_controller = kwargs.get('core_controller', None)
        self.sfc_gateway = kwargs.get('sfc_gateway', None)


class FlowClassifier(Base):
    __tablename__ = 'flow_classifiers'
    description = Column(String(255), nullable=True)
    source_cloud = Column(String(255), nullable=True)
    source_ip = Column(String(255), nullable=True)
    source_port = Column(String(255), nullable=True)
    source_host = Column(String(255), nullable=True)
    source_tap = Column(String(255), nullable=True)
    destination_cloud = Column(String(255), nullable=True)
    destination_ip = Column(String(255), nullable=True)
    destination_port = Column(String(255), nullable=True)
    destination_host = Column(String(255), nullable=True)
    destination_tap = Column(String(255), nullable=True)
    protocol = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.description = kwargs.get('description', None)
        self.source_cloud = kwargs.get('source_cloud', None)
        self.source_ip = kwargs.get('source_ip', None)
        self.source_port = kwargs.get('source_port', None)
        self.source_host = kwargs.get('source_host', None)
        self.source_tap = kwargs.get('source_tap', None)
        self.destination_cloud = kwargs.get('destination_cloud', None)
        self.destination_ip = kwargs.get('destination_ip', None)
        self.destination_port = kwargs.get('destination_port', None)
        self.destination_host = kwargs.get('destination_host', None)
        self.destination_tap = kwargs.get('destination_tap', None)
        self.protocol = kwargs.get('protocol', None)


class VirtualFunction(Base):
    cloud = Column(String(255), nullable=True)
    host = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.cloud = kwargs.get('cloud', None)
        self.host = kwargs.get('host', None)
        self.name = kwargs.get('name', None)
        self.description = kwargs.get('description', None)


class ForwardingGraph(Base):
    graph = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.graph = kwargs.get('graph', None)
        self.description = kwargs.get('description', None)


class Chain(Base):
    flow_classifier = Column(String(255), nullable=True)
    vnffg = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

    def __init__(self, *args, **kwargs):
        self.flow_classifier = kwargs.get('flow_classifier', None)
        self.vnffg = kwargs.get('vnffg', None)
        self.description = kwargs.get('description', None)
