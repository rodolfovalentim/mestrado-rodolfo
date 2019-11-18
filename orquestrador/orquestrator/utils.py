import queue
from collections import namedtuple

Edge = namedtuple('Edge', ['vertex', 'weight'])


class Switch(object):
    def __init__(self, dpid):
        self.dpid = dpid

    def __str__(self):
        return 'Switch %d'.format(self.dpid)

    def __repr__(self):
        return 'Switch {}'.format(self.dpid)


class GraphUndirectedWeighted(object):
    def __init__(self, switches):
        self.switches = switches
        self.switches_count = len(switches)
        self.adjacency_list = [[] for _ in range(len(switches))]

    def add_edge(self, source_dpid, dest_dpid, weight):
        source = [x.dpid for x in self.switches].index(source_dpid)
        dest = [x.dpid for x in self.switches].index(dest_dpid)
        self.adjacency_list[source].append(Edge(dest, weight))
        self.adjacency_list[dest].append(Edge(source, weight))

    def get_edge(self, vertex):
        for e in self.adjacency_list[vertex]:
            yield e

    def get_vertex(self):
        for v in range(self.switches_count):
            yield v

    def dijkstra(self, source_dpid, dest_dpid):
        source = [x.dpid for x in self.switches].index(source_dpid)
        dest = [x.dpid for x in self.switches].index(dest_dpid)

        q = queue.PriorityQueue()
        parents = []
        distances = []
        start_weight = float("inf")

        for i in self.get_vertex():
            weight = start_weight
            if source == i:
                weight = 0
            distances.append(weight)
            parents.append(None)

        q.put(([0, source]))

        while not q.empty():
            v_tuple = q.get()
            v = v_tuple[1]

            for e in self.get_edge(v):
                candidate_distance = distances[v] + e.weight
                if distances[e.vertex] > candidate_distance:
                    distances[e.vertex] = candidate_distance
                    parents[e.vertex] = v
                    # primitive but effective negative cycle detection
                    if candidate_distance < -1000:
                        raise Exception("Negative cycle detected")
                    q.put(([distances[e.vertex], e.vertex]))

        shortest_path = []
        end = dest
        while end is not None:
            shortest_path.append(self.switches[end])
            end = parents[end]

        shortest_path.reverse()

        return shortest_path, distances[dest]
