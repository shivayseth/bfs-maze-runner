# maze_video_export.py
# Exports exploration (red) + shortest path (green) to MP4
# Resolution capped to 1080p, aspect ratio preserved
#
# Optimisations:
#   1. Incremental numpy rendering — only new cells painted per frame, not all
#   2. Frames piped directly to FFmpeg — no PNG files written to disk

import ast
import csv
import subprocess
import time
import numpy as np
from PIL import Image
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
CELL_SIZE = 12
FPS = 30
OUTPUT_VIDEO = "maze_exploration_and_shortest_1080p.mp4"

MAX_WIDTH  = 1920
MAX_HEIGHT = 1080

WALL_COLOR    = (0,   0,   0  )
EMPTY_COLOR   = (255, 255, 255)
EXPLORE_COLOR = (220, 60,  60 )   # red
PATH_COLOR    = (60,  220, 60 )   # green

# -----------------------------
# LOAD FILES
# -----------------------------
def load_statistics():
    with open("statistics.txt") as f:
        lines = f.readlines()
    maze_file = lines[0].strip()
    for line in lines:
        if line.startswith("shortest path:"):
            return maze_file, ast.literal_eval(line.split(":", 1)[1])
    raise ValueError("No shortest path found")

def load_exploration():
    with open("exploration.csv") as f:
        reader = csv.DictReader(f)
        return [(int(r["x-coordinate"]), int(r["y-coordinate"])) for r in reader]

def load_maze(filename):
    with open(filename) as f:
        return [list(line.rstrip("\n")) for line in f]

# -----------------------------
# COORDINATE HELPERS
# -----------------------------
def cell_to_ascii(x, y, maze_height):
    r = (maze_height - 1 - y) * 2 + 1
    c = x * 2 + 1
    return r, c

def paint(arr, r, c, color, cell_size, scale, base=None):
    """Paint one ASCII cell onto a numpy (H, W, 3) array.
    If base is provided, wall pixels (black in base) are never overwritten."""
    x0 = int(c * cell_size * scale)
    y0 = int(r * cell_size * scale)
    x1 = int((c + 1) * cell_size * scale)
    y1 = int((r + 1) * cell_size * scale)
    if base is None:
        arr[y0:y1, x0:x1] = color
    else:
        # Only paint pixels that are not walls in the base maze
        mask = np.all(base[y0:y1, x0:x1] != [0, 0, 0], axis=-1)
        arr[y0:y1, x0:x1][mask] = color

# -----------------------------
# MAIN
# -----------------------------
def main():
    maze_file, shortest_path = load_statistics()
    exploration_path         = load_exploration()
    maze                     = load_maze(maze_file)

    maze_rows   = len(maze)
    maze_cols   = len(maze[0])
    maze_h_cells = (maze_rows - 1) // 2

    base_w = maze_cols * CELL_SIZE
    base_h = maze_rows * CELL_SIZE
    scale  = min(MAX_WIDTH / base_w, MAX_HEIGHT / base_h, 1.0)

    width_px  = int(base_w * scale) // 2 * 2
    height_px = int(base_h * scale) // 2 * 2

    # ---- Build base maze as numpy array once ----
    print("🖼  Building base maze array...")
    base = np.full((height_px, width_px, 3), EMPTY_COLOR, dtype=np.uint8)
    for r in range(maze_rows):
        for c in range(maze_cols):
            if maze[r][c] == "#":
                paint(base, r, c, WALL_COLOR, CELL_SIZE, scale)

    total_frames = len(exploration_path) + len(shortest_path)
    print(f"🎥 Streaming {total_frames} frames → FFmpeg (no disk I/O)")
    print(f"📐 Resolution: {width_px}x{height_px} @ {FPS} FPS")

    # ---- Open FFmpeg process, accept raw RGB on stdin ----
    ffmpeg = subprocess.Popen(
        [
            "ffmpeg", "-y",
            "-f",        "rawvideo",
            "-pix_fmt",  "rgb24",
            "-s",        f"{width_px}x{height_px}",
            "-r",        str(FPS),
            "-i",        "-",
            "-c:v",      "libx264",
            "-pix_fmt",  "yuv420p",
            "-crf",      "18",
            "-preset",   "slow",
            OUTPUT_VIDEO,
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,   # suppress FFmpeg log spam
    )

    start_time    = time.time()
    explored_cells = set()

    # Working arrays — mutated incrementally, never rebuilt from scratch
    explore_arr = base.copy()   # grows red cells
    path_arr    = None          # set after exploration finishes

    with tqdm(total=total_frames, unit="frame") as bar:

        # ---- EXPLORATION PHASE (red) ----
        for x, y in exploration_path:
            r, c = cell_to_ascii(x, y, maze_h_cells)

            # Paint the cell
            paint(explore_arr, r, c, EXPLORE_COLOR, CELL_SIZE, scale, base=base)
            explored_cells.add((x, y))

            # Paint corridor to each already-explored neighbour only
            # (guarantees we only connect adjacent cells — fixes checkerboard)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in explored_cells:
                    r2, c2 = cell_to_ascii(nx, ny, maze_h_cells)
                    paint(explore_arr, (r + r2) // 2, (c + c2) // 2,
                          EXPLORE_COLOR, CELL_SIZE, scale, base=base)

            # Stream frame as raw bytes — no PNG encoding, no disk write
            ffmpeg.stdin.write(explore_arr.tobytes())
            bar.update(1)

        # ---- SHORTEST PATH PHASE (green, drawn over frozen exploration) ----
        path_arr = explore_arr.copy()   # snapshot full exploration

        for i, (x, y) in enumerate(shortest_path):
            r, c = cell_to_ascii(x, y, maze_h_cells)
            paint(path_arr, r, c, PATH_COLOR, CELL_SIZE, scale, base=base)

            if i > 0:
                px, py = shortest_path[i - 1]
                r2, c2 = cell_to_ascii(px, py, maze_h_cells)
                paint(path_arr, (r + r2) // 2, (c + c2) // 2,
                      PATH_COLOR, CELL_SIZE, scale, base=base)

            ffmpeg.stdin.write(path_arr.tobytes())
            bar.update(1)

    ffmpeg.stdin.close()
    ffmpeg.wait()

    elapsed = time.time() - start_time
    print(f"\n✅ Done in {elapsed:.1f}s — saved as {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()