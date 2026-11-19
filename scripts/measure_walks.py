"""Measure the first visible surfaces along both saved camera tracks, at every frame."""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from walks import SCREEN_START, SCREEN_END, GAP_START, GAP_END, FPS, SPEED, GAP_START_X

p = argparse.ArgumentParser()
p.add_argument("--out", type=Path, required=True)
args = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
args.out.mkdir(parents=True, exist_ok=True)
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y = 1320, 820
assert s.render.fps == FPS and s.render.fps_base == 1
W, H = 330, 205
screen = set(
    next(
        c for c in bpy.data.collections["Screens"].children if c.name.startswith("一")
    ).all_objects
)
subjects = {}
for key, name in [
    ("dancer", "王屋山"),
    ("drummer", "韩熙载·击鼓"),
    ("farewell", "韩熙载·持槌"),
]:
    subjects[key] = next(
        o for o in s.objects if name in o.name and "彩墨浅浮雕" in o.name
    )


def visible_geometry(skip_screen):
    vertices, polygons, owners = [], [], []
    graph = bpy.context.evaluated_depsgraph_get()
    for group in (
        "Sections",
        "Screens",
        "Characters",
        "Furniture",
        "Props",
        "GapCorridor",
    ):
        for o in bpy.data.collections[group].all_objects:
            if o.type not in ("CURVE", "MESH") or (skip_screen and o in screen):
                continue
            ob = o.evaluated_get(graph)
            mesh = ob.to_mesh()
            offset = len(vertices)
            vertices.extend(ob.matrix_world @ v.co for v in mesh.vertices)
            polygons.extend(
                tuple(offset + i for i in poly.vertices) for poly in mesh.polygons
            )
            owners.extend([o] * len(mesh.polygons))
            ob.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons), owners


full = visible_geometry(False)
without = visible_geometry(True)


def hits(obj, geometry):
    tree, owners = geometry
    cam = s.camera
    corners = [
        world_to_camera_view(s, cam, obj.matrix_world @ Vector(v))
        for v in obj.bound_box
    ]
    # The projected box is a conservative crop if it is fully in front of the eye.
    if min(v.z for v in corners) > 0:
        x1 = max(0, math.floor(W * min(v.x for v in corners)))
        x2 = min(W, math.ceil(W * max(v.x for v in corners)))
        y1 = max(0, math.floor(H * min(v.y for v in corners)))
        y2 = min(H, math.ceil(H * max(v.y for v in corners)))
    else:
        x1, x2, y1, y2 = 0, W, 0, H
    tr, br, bl, tl = [cam.matrix_world @ v for v in cam.data.view_frame(scene=s)]
    dx, dy = (br - bl) / W, (tl - bl) / H
    origin = cam.matrix_world.translation
    count = 0
    for y in range(y1, y2):
        base = bl - origin + dy * (y + 0.5)
        for x in range(x1, x2):
            index = tree.ray_cast(origin, (base + dx * (x + 0.5)).normalized(), 60)[2]
            if index is not None and owners[index] == obj:
                count += 1
    return count


screen_views = {}
for frame in (25, 49):
    s.frame_set(frame)
    screen_views[str(frame)] = {
        k: [hits(subjects[k], g) for g in (full, without)]
        for k in ("dancer", "drummer")
    }
before, after = screen_views["25"], screen_views["49"]
assert before["dancer"][0] == before["dancer"][1] > 0
assert before["drummer"][0] == 0 < before["drummer"][1]
assert all(on == off and on > 0 for on, off in after.values())
rows = []
for frame in range(SCREEN_START, SCREEN_END + 1):
    s.frame_set(frame)
    cam = s.camera
    assert cam.name.startswith("10") and abs(cam.location.z - 1.59) < 1e-5
    rows.append(
        [
            "screen",
            frame,
            round(cam.location.x, 5),
            round(cam.location.y, 5),
            hits(subjects["dancer"], full),
            hits(subjects["drummer"], full),
            "",
        ]
    )
gap_rows = []
for frame in range(GAP_START, GAP_END + 1):
    s.frame_set(frame)
    cam = s.camera
    assert cam.name.startswith("11") and abs(cam.location.z - 1.59) < 1e-5
    assert (
        abs(cam.location.x - (GAP_START_X - (frame - GAP_START) * SPEED / FPS)) < 1e-5
        and abs(cam.location.y + 1.70) < 1e-5
    )
    row = [
        "gap",
        frame,
        round(cam.location.x, 5),
        round(cam.location.y, 5),
        "",
        "",
        hits(subjects["farewell"], full),
    ]
    gap_rows.append(row)
rows.extend(gap_rows)
gap = round(s["gap_length_m"], 2)
stem = f"walk-{gap:.2f}"
with (args.out / (stem + ".csv")).open("w", newline="") as file:
    out = csv.writer(file, lineterminator="\n")
    out.writerow(
        [
            "track",
            "frame",
            "eye_x_m",
            "eye_y_m",
            "dancer_hits",
            "drummer_hits",
            "farewell_host_hits",
        ]
    )
    out.writerows(rows)


def observation(row):
    if row is None:
        return None
    return dict(
        frame=row[1],
        seconds=round((row[1] - GAP_START) / FPS, 4),
        x_m=row[2],
        hits=row[-1],
    )


entry_x = -7.05
exit_x = round(entry_x - gap, 2)


def crossing(x):
    return dict(
        exact_seconds=round((GAP_START_X - x) / SPEED, 3),
        sample=observation(next(r for r in gap_rows if r[2] <= x)),
    )


summary = dict(
    grid=[W, H],
    fps=FPS,
    speed_m_s=SPEED,
    eye_z_m=1.59,
    gap_m=gap,
    screen_views_on_off=screen_views,
    entry=crossing(entry_x),
    exit=crossing(exit_x),
    first_samples_by_min_hits={
        str(n): observation(next((r for r in gap_rows if r[-1] >= n), None))
        for n in (1, 170, 508, 677)
    },
    first_drummer_on_screen_walk=next(
        r[1] for r in rows if r[0] == "screen" and r[5] > 0
    ),
)
(args.out / (stem + ".json")).write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
)
print(summary)
