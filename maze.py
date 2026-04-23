#maze.py
#Contains the Maze class, wall storage, BFS movement logic,BFS exploration,
#and BFS shortest-path extension logic.
from runner import (  # type: ignore
    create_runner,
    get_x,
    get_y,
    turn,
    get_orientation,
    forward,
)
class Maze:
    def __init__(self,width=5, height=5):
        #store maze dimensions
        self._width = width
        self._height= height
        #sets store internal walls for lookup
        #horizontal: (x, hline)
        #vertical: (y, vline)
        self.horizontal_walls= set()
        self.vertical_walls= set()
    @property
    def width(self):
        #returns width of maze
        return self._width 
    @property
    def height(self):
        #returns height of maze
        return self._height
    def add_horizontal_wall(self, x_coordinate, horizontal_line):
        #add horizontal wall segment
        self.horizontal_walls.add((x_coordinate,horizontal_line))
    def add_vertical_wall(self, y_coordinate, vertical_line):
        #add vertical wall segment
        self.vertical_walls.add((y_coordinate,vertical_line))
    def get_walls(self, x_coordinate: int, y_coordinate: int) -> tuple[bool, bool, bool, bool]:
        #determine walls around (x, y): N, E, S, W
        x= x_coordinate
        y= y_coordinate
        north=False
        south=False
        east=False
        west=False
        #check north (top boundary or internal horizontal wall)
        if y== self.height-1:
            north= True
        else:
            north = (x, y + 1) in self.horizontal_walls
        #check east (right boundary or internal vertical wall)
        if x== self.width-1:
            east= True
        else:
            east = (y, x + 1) in self.vertical_walls   
        #check south (bottom boundary or internal horizontal wall)
        if y==0:
            south =True
        else:
            south = (x, y) in self.horizontal_walls
        #check west (left boundary or internal vertical wall)
        if x==0:
            west = True
        else:
            west = (y, x) in self.vertical_walls
        return(north,east,south,west)

    def move(self, x, y):
        #returns all BFS-valid neighbour cells that are not blocked by walls
        neighbours = []

        N, E, S, W = self.get_walls(x, y)

        # north
        if not N:
            neighbours.append((x, y + 1))

        # south
        if not S:
            neighbours.append((x, y - 1))

        # east
        if not E:
            neighbours.append((x + 1, y))

        # west
        if not W:
            neighbours.append((x - 1, y))

        return neighbours

    def explore(self, start, goal):
        #BFS queue
        queue = [start]

        #visited set
        visited = {start}

        #parent map for reconstructing shortest path
        parent = {}

        #BFS order for logging
        bfs_order = [start]

        #BFS loop
        while queue:
            x, y = queue.pop(0)

            #stop when goal is reached
            if (x, y) == goal:
                break

            #explore neighbours using BFS move()
            for nx, ny in self.move(x, y):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (x, y)
                    queue.append((nx, ny))
                    bfs_order.append((nx, ny))

        #return both values
        return parent, bfs_order
    def shortest_path(self, start=None, goal=None):
        #compute shortest path between start and goal using BFS

        #default start is bottom-left corner
        if start is None:
            start = (0, 0)

        #default goal is top-right corner
        if goal is None:
            goal = (self.width - 1, self.height - 1)

        #run BFS exploration and get the parent mapping
        parent, _ = self.explore(start, goal)

        #if goal was never reached and goal is not the start itself
        if goal not in parent and goal != start:
            raise ValueError("No valid path found using BFS.")

        #reconstruct path by walking backwards from goal to start
        path = [goal]
        curr = goal

        #walk through parent links until we reach the start
        while curr != start:
            curr = parent[curr]
            path.append(curr)

        #reverse to get path from start to goal
        path.reverse()
        return path
