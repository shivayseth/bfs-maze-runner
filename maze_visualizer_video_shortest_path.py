# maze_visualizer_shortest_path.py
# Exports shortest path (green) to MP4
# Resolution capped to 1080p, aspect ratio preserved
#
# Optimisations:
#   1. Base maze rendered once as numpy array
#   2. Incremental rendering — only new cells painted per frame
#   3. Frames piped directly to FFmpeg — no PNG files written to disk
#   4. Wall pixels never overwritten (mask applied on every paint)

import ast
import subprocess
import time
import numpy as np
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
CELL_SIZE   = 12
FPS         = 30
OUTPUT_VIDEO = "shortest_path_1080p.mp4"

MAX_WIDTH  = 1920
MAX_HEIGHT = 1080

WALL_COLOR  = (0,   0,   0  )
EMPTY_COLOR = (255, 255, 255)
PATH_COLOR  = (60,  220, 60 )   # green
MOUSE_COLOR = (50,  150, 255)   # blue dot showing current position

# -----------------------------
# LOAD FILES
# -----------------------------
def load_statistics():
    with open("statistics.txt") as f:
        lines = f.readlines()
    maze_file = lines[0].strip()
    for line in lines:
        if line.startswith("shortest path:"):
            return maze_file, ast.literal_eval(line.split(":", 1)[1].strip())
    raise ValueError("No shortest path found")

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
    """Paint one ASCII cell. If base provided, wall pixels are never overwritten."""
    x0 = int(c * cell_size * scale)
    y0 = int(r * cell_size * scale)
    x1 = int((c + 1) * cell_size * scale)
    y1 = int((r + 1) * cell_size * scale)
    if base is None:
        arr[y0:y1, x0:x1] = color
    else:
        mask = np.all(base[y0:y1, x0:x1] != [0, 0, 0], axis=-1)
        arr[y0:y1, x0:x1][mask] = color

# -----------------------------
# MAIN
# -----------------------------
def main():
    maze_file, shortest_path = load_statistics()
    maze = load_maze(maze_file)

    maze_rows    = len(maze)
    maze_cols    = len(maze[0])
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

    total_frames = len(shortest_path)
    print(f"🎥 Streaming {total_frames} frames → FFmpeg (no disk I/O)")
    print(f"📐 Resolution: {width_px}x{height_px} @ {FPS} FPS")

    # ---- Open FFmpeg, accept raw RGB on stdin ----
    ffmpeg = subprocess.Popen(
        [
            "ffmpeg", "-y",
            "-f",       "rawvideo",
            "-pix_fmt", "rgb24",
            "-s",       f"{width_px}x{height_px}",
            "-r",       str(FPS),
            "-i",       "-",
            "-c:v",     "libx264",
            "-pix_fmt", "yuv420p",
            "-crf",     "18",
            "-preset",  "slow",
            OUTPUT_VIDEO,
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    start_time = time.time()
    path_arr   = base.copy()   # incremental array — walls preserved via mask

    with tqdm(total=total_frames, unit="frame") as bar:
        for i, (x, y) in enumerate(shortest_path):
            r, c = cell_to_ascii(x, y, maze_h_cells)

            # Paint corridor from previous cell
            if i > 0:
                px, py  = shortest_path[i - 1]
                r2, c2  = cell_to_ascii(px, py, maze_h_cells)
                paint(path_arr, (r + r2) // 2, (c + c2) // 2,
                      PATH_COLOR, CELL_SIZE, scale, base=base)
                # Also finalise previous cell as path (remove mouse colour)
                paint(path_arr, r2, c2, PATH_COLOR, CELL_SIZE, scale, base=base)

            # Draw mouse at current position
            frame = path_arr.copy()
            paint(frame, r, c, MOUSE_COLOR, CELL_SIZE, scale, base=base)

            ffmpeg.stdin.write(frame.tobytes())
            bar.update(1)

    ffmpeg.stdin.close()
    ffmpeg.wait()

    elapsed = time.time() - start_time
    print(f"\n✅ Done in {elapsed:.1f}s — saved as {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()