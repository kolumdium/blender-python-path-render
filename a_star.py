import heapq
from collections import defaultdict
import converter as cv

class AStar:
    def __init__(self, adj_list, node_coordinates):
        self.adj_list = adj_list
        self.node_coordinates = node_coordinates
        self.open_heap = []
        self.came_from = {}
        self.g_score = defaultdict(lambda: float('inf'))
        self.source = None
        self.destination = None
        

    def initialize(self, source , destination):
        heapq.heappush(self.open_heap, (0 + self.heuristic(source, destination), 0, source)) # (f_score, g_score, node)
        self.destination = destination
        self.source = source
        self.g_score[source] = 0

    def heuristic(self, a, b):
        point = self.node_coordinates[a]
        goal = self.node_coordinates[b]
        return cv.get_distance_haversine(point[0], point[1], goal[0], goal[1])
        # return math.sqrt((point[0] - goal[0]) ** 2 + (point[1] - goal[1]) ** 2)

    def get_neighbors(self, v):
            return self.adj_list[v].items()

    def step(self):

        if not self.open_heap:
            return False  # No path found, and open list is exhausted

        current_f, current_g, current = heapq.heappop(self.open_heap)

        if current == self.destination:
            return False  # Path found

        for neighbor, weight in self.get_neighbors(current):
            tentative_g = current_g + weight
            if tentative_g < self.g_score[neighbor]:
                self.came_from[neighbor] = current
                self.g_score[neighbor] = tentative_g
                f_score = tentative_g + self.heuristic(neighbor, self.destination)

                heapq.heappush(self.open_heap, (f_score, tentative_g, neighbor))

        return True  # Algorithm still running


    def get_explored_nodes(self):
        return self.came_from.keys()

    def reconstruct_path(self, current=None):
        if current is None:
            current = self.destination
        path = []
        while current in self.came_from:
            path.append(current)
            current = self.came_from[current]
        path.append(self.source)
        return path[::-1]

# Usage:
# astar = AStar(adj_list, node_coordinates)
# astar.initialize(source_node, destination_node)
# while astar.step():
#     pass  # Run the algorithm step by step until finished
# explored_nodes = astar.get_explored_nodes()
# print("Explored nodes:", explored_nodes)
# path = astar.reconstruct_path()
# print("Shortest path:", path)
