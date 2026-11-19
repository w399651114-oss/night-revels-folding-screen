"""Render the study views from the open .blend using Cycles."""

import argparse
from pathlib import Path
import sys
import bpy

p = argparse.ArgumentParser()
p.add_argument(
    "--out", type=Path, default=Path(__file__).resolve().parents[1] / "renders"
)
p.add_argument("--percent", type=int, default=100)
p.add_argument("--samples", type=int, default=24)
p.add_argument("--views", default="1,2,3,4,5,6,7,8,9")
p.add_argument(
    "--frames", help="Comma-separated timeline frames for the walking experiment"
)
p.add_argument(
    "--omit-first-screen",
    action="store_true",
    help="Hide the first partition for this unsaved render session",
)
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
a.out.mkdir(exist_ok=True, parents=True)
s = bpy.context.scene
names = [
    "overview",
    "screen-before",
    "screen-after",
    "gap",
    "listening",
    "winds",
    "table-detail",
    "rest",
    "farewell",
]
if a.omit_first_screen:
    screen = next(
        c for c in bpy.data.collections["Screens"].children if c.name.startswith("一")
    )
    screen.hide_render = True
if a.frames:
    views = [(int(v), f"f{int(v):03}", False) for v in a.frames.split(",")]
else:
    views = [
        (1 + (i - 1) * 24, names[i - 1], i == 1) for i in map(int, a.views.split(","))
    ]
for frame, name, wide in views:
    s.frame_set(frame)
    s.cycles.samples = a.samples
    s.render.resolution_x, s.render.resolution_y = (1820, 650) if wide else (1320, 820)
    s.render.resolution_percentage = a.percent
    s.render.filepath = str((a.out / (name + ".png")).resolve())
    bpy.ops.render.render(write_still=True)
