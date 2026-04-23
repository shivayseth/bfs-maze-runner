#maze_runner.py
#Handles maze file loading, command-line parsing, exploration logging,
#and statistics output for the Maze Runner system.
from maze import Maze
from runner import turn, forward, create_runner
import argparse
import sys
def maze_reader(maze_file: str):
    #read maze file and convert to Maze object
    try:
        with open(maze_file, "r") as f:
            lines = [line.rstrip("\n") for line in f]

        #all lines must have the same length
        expected = len(lines[0])
        for line in lines:
            if len(line) != expected:
                raise ValueError("Inconsistent line lengths")
    except OSError:
        raise IOError("Could not read maze file.")

    #must have at least top border, one interior row, and bottom border
    if len(lines) < 3:
        raise ValueError("Invalid maze file: too small")

    overall_height = len(lines)        #number of rows in file
    overall_width  = len(lines[0])     #number of columns in file

    #validating maze dimensions
    if overall_height % 2 == 0 or overall_width % 2 == 0:
        raise ValueError("Invalid maze dimensions")

    #maze dimensions (number of cells in x and y)
    height = (overall_height - 1) // 2
    width  = (overall_width  - 1) // 2

    maze = Maze(width, height)

    #check that the outer rectangle is all walls
    if any(c != "#" for c in lines[0]):
        raise ValueError("Top wall missing")
    if any(c != "#" for c in lines[-1]):
        raise ValueError("Bottom wall missing")
    for row in lines[1:-1]:
        if row[0] != "#" or row[-1] != "#":
            raise ValueError("Side wall missing")
        
    #internal horizontal walls:
    #Horizontal wall rows appear at even indices (0,2,4,...)
    #we skip the outer ones (i = 0 and last), so start at 2 and stop at overall_height-1
    for i in range(2, overall_height - 1, 2):
        #map file row index to horizontal line number (hline) in maze coords
        hline = (overall_height - 1 - i) // 2
        # odd columns (1,3,5,...) are horizontal segments between cells
        for j in range(1, overall_width - 1, 2):
            if lines[i][j] == "#":
                x = j // 2                  #cell x-position
                maze.add_horizontal_wall(x, hline)

    #internal vertical walls:
    #odd-indexed rows are cell rows with vertical wall segments
    for i in range(1, overall_height - 1, 2):
        #map file row index to cell y-coordinate in maze coords
        y = (overall_height - 1 - i) // 2
        #even columns (2,4,6,...) are vertical wall segments
        for j in range(2, overall_width - 1, 2):
            if lines[i][j] == "#":
                vline = j // 2              #vertical line index between cells
                maze.add_vertical_wall(y, vline)

    return maze

def parse_position(text: str = None):
    #convert "x,y" into tuple(int, int)
    if text is None:
        return None
    x_str, y_str = text.split(",")
    return int(x_str.strip()), int(y_str.strip())


def run_and_log(maze, starting, goal, maze_filename):

    # Starting position
    if starting is None:
        start = (0, 0)
    else:
        start = starting


    parent, bfs_order= maze.explore(start, goal)

    # bfs_order is the list of cells in the order BFS discovered them
    steps = len(bfs_order)

    #Reconstruct shortest path

    sp = maze.shortest_path(start, goal)
    plen = len(sp)

    score = steps / 4 + plen

    with open("exploration.csv", "w") as f:
        f.write("Step,x-coordinate,y-coordinate,Actions\n")
        step_num = 1
        for (x, y) in bfs_order:
            f.write(f"{step_num},{x},{y},BFS\n")  # BFS does not use LF/RF/F actions
            step_num += 1

    with open("statistics.txt", "w") as f:
        f.write(f"{maze_filename}\n")
        f.write(f"score: {score}\n")
        f.write(f"steps: {steps}\n")
        f.write(f"shortest path: {sp}\n")
        f.write(f"length of shortest path: {plen}\n")

if __name__ == "__main__":
    #command-line interface (CLI) for the Maze Runner
    parser = argparse.ArgumentParser(description="ECS Maze Runner")
    parser.add_argument("maze")
    parser.add_argument("--starting", default=None)
    parser.add_argument("--goal", default=None)
    args = parser.parse_args()

    #attempt to load maze
    try:
        maze = maze_reader(args.maze)
    except (IOError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    #parse starting and goal positions
    try:
        if args.starting is None:
            start = (0, 0)
        else:
            start = parse_position(args.starting)

        if args.goal is None:
            goal = (maze.width - 1, maze.height - 1)
        else:
            goal = parse_position(args.goal)
        #bounds checking
        if not (0 <= start[0] < maze.width and 0 <= start[1] < maze.height):
            raise ValueError("Starting position out of bounds")
        if not (0 <= goal[0] < maze.width and 0 <= goal[1] < maze.height):
            raise ValueError("Goal position out of bounds")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    print("Shortest path:", maze.shortest_path(start, goal))
    #run exploration + stats + logs
    run_and_log(maze, start, goal, args.maze)
