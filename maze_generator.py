import random
import sys
import time

WIDTH = int(input("Width of Maze: "))
HEIGHT = int(input("Height of Maze: "))

if WIDTH <= 50 and HEIGHT <= 50:
    size = 'small'
elif 50 < WIDTH <= 100 and 50 < HEIGHT <= 100:
    size = 'medium'
elif 100 < WIDTH <= 200 and 100 < HEIGHT <= 200:
    size = 'large'
elif 200 < WIDTH <= 1000 and 200 < HEIGHT <= 1000:
    size = 'huge'
elif 1000 < WIDTH <= 5000 and 1000 < HEIGHT <= 5000:
    size = 'massive'
else:
    print("Maze size too large! Please choose dimensions <= 5000.")
    sys.exit(1)

def add_loops(maze, width, height, loop_chance=0.08):
    # loop_chance = probability of removing a wall (8% is good)

    rows = 2 * height + 1
    cols = 2 * width + 1

    for y in range(height):
        for x in range(width):
            r = (height - 1 - y) * 2 + 1
            c = x * 2 + 1

            # try breaking east wall
            if x < width - 1 and random.random() < loop_chance:
                if maze[r][c + 1] == "#":
                    maze[r][c + 1] = "."

            # try breaking north wall
            if y < height - 1 and random.random() < loop_chance:
                if maze[r - 1][c] == "#":
                    maze[r - 1][c] = "."
def generate_maze(width, height, loop_chance=0.15):
    visited = [[False] * width for _ in range(height)]

    rows = 2 * height + 1
    cols = 2 * width + 1
    maze = [["#"] * cols for _ in range(rows)]

    def cell_to_ascii(x, y):
        r = (height - 1 - y) * 2 + 1
        c = x * 2 + 1
        return r, c

    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        x, y = stack[-1]
        r, c = cell_to_ascii(x, y)
        maze[r][c] = "."

        neighbours = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                neighbours.append((nx, ny))

        if neighbours:
            nx, ny = random.choice(neighbours)
            visited[ny][nx] = True

            r2, c2 = cell_to_ascii(nx, ny)
            maze[(r + r2)//2][(c + c2)//2] = "."

            stack.append((nx, ny))
        else:
            stack.pop()

    # -------- ADD LOOPS --------
    for y in range(height):
        for x in range(width):
            if random.random() < loop_chance:
                dx, dy = random.choice([(1,0),(0,1)])
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    r1, c1 = cell_to_ascii(x, y)
                    r2, c2 = cell_to_ascii(nx, ny)
                    maze[(r1 + r2)//2][(c1 + c2)//2] = "."

    return maze


def write_maze(filename, maze):
    with open(filename, "w") as f:
        for row in maze:
            f.write("".join(row) + "\n")


if __name__ == "__main__":
    print(f"Generating {WIDTH}x{HEIGHT} maze...")

    start_time = time.perf_counter()

    maze = generate_maze(WIDTH, HEIGHT, loop_chance=0.15)
    add_loops(maze, WIDTH, HEIGHT)
    write_maze(f"{size}_{WIDTH}x{HEIGHT}.mz", maze)

    end_time = time.perf_counter()
    elapsed = end_time - start_time

    print(f"Done! Saved as {size}_{WIDTH}x{HEIGHT}.mz")
    print(f"Generation time: {elapsed:.2f} seconds")