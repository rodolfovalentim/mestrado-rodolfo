from cloud import VirtualMachine

class VirtualNetworkFunction(VirtualMachine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nf_type = kwargs.get('nf_type', None)
        self.nfvi_pop = kwargs.get('nfvi_pop', None)
    
    def __repr__(self):
        return 'Virtual Machine {}'.format(self.__dict__)

    def get_ip(self):
        if len(self.taps) > 0:
            return self.taps[0].get_ip()

    def get_cloud(self):
        return self.cloud

class FowardingGraphDomain(object):
    '''
        Graph inside domain
    '''
    def __init__(self, *args, **kwargs):
        self.id = kwargs.get('id', None)
        self.nfvi_pop = kwargs.get('nfvi_pop', None)
        self.ordered_vnfs = kwargs.get('ordered_vnfs', [])
        self.ordered_target_switches = kwargs.get('ordered_vnfs', [])
        self.prev_fgd = kwargs.get('prev_fgd', None)      
        self.next_fgd = kwargs.get('next_fgd', None)
        
        self.intradomain_hops = kwargs.get('intradomain_hops', [])
        
    def __repr__(self):
        return "< Fowarding Graph Domain {} >".format(self.__dict__)
        
class FowardingGraphHop(object):
    def __init__(self, *args, **kwargs):
        self.flow_classifier = kwargs.get('flow_classifier', None)
        self.switch_graph = kwargs.get('switch_graph', None)        
        self.prev_hop_id = kwargs.get('prev_hop_id', None)        
        self.hop_id = kwargs.get('hop_id', None)                
        self.src_vnf = kwargs.get('src_vnf', None)
        self.dest_vnf = kwargs.get('src_vnf', None)
        self.src_gateway = kwargs.get('src_gateway', None)
        self.dest_gateway = kwargs.get('dest_gateway', None)
        self.src_flow = kwargs.get('src_flow', None)
        self.dest_flow = kwargs.get('dest_flow', None)
        
    def __repr__(self):
        return "< Fowarding Graph Hop {} >".format(self.__dict__)