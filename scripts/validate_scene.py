"""Validate a saved project and optionally compare its geometry with a prior report."""

from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p = argparse.ArgumentParser()
p.add_argument("--report", type=Path)
p.add_argument(
    "--layout", type=Path, help="Write world extents for a paired layout check"
)
p.add_argument("--compare", type=Path)
p.add_argument(
    "--portable",
    action="store_true",
    help="Compare semantic measurements across Blender platforms",
)
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
s = bpy.context.scene
groups = (
    "Sections",
    "Screens",
    "Furniture",
    "Characters",
    "Props",
    "Lights",
    "GapCorridor",
    "StudyViews",
)
assert all(bpy.data.collections.get(g) for g in groups)
assert s.unit_settings.system == "METRIC" and s.unit_settings.scale_length == 1
assert s["seed"] == s.cycles.seed == 963
slab = next(o for o in bpy.data.collections["Sections"].objects if "长卷基面" in o.name)
gap_length = round(s["gap_length_m"], 2)
assert gap_length in (1.10, 3.30)
delta = round(3.30 - gap_length, 2)
gap_exit = round(-7.05 - gap_length, 2)
gap = next(
    ob for ob in bpy.data.collections["GapCorridor"].objects if "x_limits_m" in ob
)
assert all(abs(x - y) < 1e-4 for x, y in zip(gap["x_limits_m"], [gap_exit, -7.05]))
seams = sorted(
    ob.location.x
    for ob in bpy.data.collections["GapCorridor"].objects
    if "素绢接缝" in ob.name
)
assert (
    len(seams) == 2
    and abs(seams[0] - gap_exit + 0.004) < 1e-4
    and abs(seams[1] + 7.046) < 1e-4
)
assert (
    abs(slab.dimensions.x - (29.4 - delta)) < 0.001
    and abs(slab.dimensions.y - 4.4) < 0.001
)
image = bpy.data.images["scroll.jpg"]
assert image.packed_file and image.size[:] == (13898, 1200)
assert all(p.filepath.startswith("//") for p in image.packed_files)
graph = bpy.context.evaluated_depsgraph_get()
from functools import lru_cache


@lru_cache(None)
def bounds(o):
    ob = o.evaluated_get(graph)
    m = ob.to_mesh()
    v = [ob.matrix_world @ p.co for p in m.vertices]
    ob.to_mesh_clear()
    return [min(p[i] for p in v) for i in range(3)], [
        max(p[i] for p in v) for i in range(3)
    ]


solids = [
    o
    for group in ("Screens", "Furniture", "Props", "Characters")
    for o in bpy.data.collections[group].all_objects
    if o.type in ("MESH", "CURVE")
]
min_y = 100
for o in solids:
    lo, hi = bounds(o)
    assert lo[0] >= -14.701 + delta and hi[0] <= 14.701, (o.name, "stage X", lo, hi)
    assert lo[2] >= -0.008, (o.name, "floor", lo)
    assert hi[0] <= gap_exit or lo[0] >= -7.05, (o.name, "gap occupied", lo, hi)
    if hi[2] > 0.01 and lo[2] < 1.82:
        min_y = min(min_y, lo[1])
assert min_y - (-2.2) > 0.60, min_y
panels = list(bpy.data.collections["Screens"].children)
heights = [max(bounds(o)[1][2] for o in c.objects) for c in panels]
assert all(abs(h - 2.2) < 0.001 for h in heights)
trees = []
for o in bpy.data.collections["Screens"].all_objects:
    if o.type == "MESH":
        trees.append((o, BVHTree.FromObject(o, graph)))


def ray(x, y, z, end):
    origin = Vector((x, y, z))
    direction = Vector((-1, 0, 0))
    hits = []
    for ob, tree in trees:
        inv = ob.matrix_world.inverted()
        pos, _, _, dist = tree.ray_cast(inv @ origin, inv.to_3x3() @ direction, x - end)
        if pos is not None:
            hits.append((round(dist, 4), ob.name))
    return min(hits) if hits else None


center = ray(9.6, 0.45, 1.59, 7.65)
side = ray(9.6, -1.70, 1.59, 7.65)
assert center and side is None, (center, side)
assert all(ray(9.6, y, 1.59, 7.65) for y in [-0.40, 0.45, 1.25])
actors = [o for o in s.objects if o.get("role") == "figure"]
reliefs = [next(ch for ch in o.children if "彩墨浅浮雕" in ch.name) for o in actors]
for o in reliefs:
    assert (
        len(o.data.polygons) > 80
        and o.data.uv_layers
        and o.data.materials[0].name.startswith("宋摹本")
    )
assert len({o["section"] for o in actors if "韩熙载" in o.name}) == 5
assert len([o for o in actors if o.name.startswith("清吹")]) == 5


def world_tree(o):
    ob = o.evaluated_get(graph)
    mesh = ob.to_mesh()
    tree = BVHTree.FromPolygons(
        [ob.matrix_world @ v.co for v in mesh.vertices],
        [p.vertices[:] for p in mesh.polygons],
    )
    ob.to_mesh_clear()
    return tree


furnishings = [
    (o, world_tree(o))
    for o in bpy.data.collections["Furniture"].all_objects
    if o.type in ("MESH", "CURVE")
]
crossings = []
for o in reliefs:
    tree = world_tree(o)
    for f, ft in furnishings:
        if tree.overlap(ft):
            crossings.append((o.name, f.name))
assert not crossings, crossings
assert len(bpy.data.cameras) == len(s.timeline_markers) == 11
assert {m.frame for m in s.timeline_markers} == {
    1,
    25,
    49,
    73,
    97,
    121,
    145,
    169,
    193,
    217,
    337,
}
assert len({actor["source_id"] for actor in actors}) == 43
for actor, relief in zip(actors, reliefs):
    assert actor["source_id"] == relief["source_id"]

# Exercise a normal Outliner edit and restore it before fingerprinting.
host = s.objects["韩熙载·击鼓"]
mallets = sorted(
    (o for o in s.objects if o.name.startswith("击鼓槌")), key=lambda o: o.name
)
assert len(mallets) == 2 and all(o.parent == host for o in mallets)
drum = s.objects["羯鼓 · 鼓座"]
before = [ob.matrix_world.copy() for ob in [*mallets, drum]]
original = host.location.copy()
try:
    host.location.x += 0.50
    bpy.context.view_layer.update()
    shifts = []
    for ob, mat, expected in zip([*mallets, drum], before, [0.5, 0.5, 0.0]):
        target = mat.copy()
        target.translation.x += expected
        assert (
            max(
                abs(ob.matrix_world[i][j] - target[i][j])
                for i in range(4)
                for j in range(4)
            )
            < 1e-5
        ), ob.name
        shifts.append(round(ob.matrix_world.translation.x - mat.translation.x, 3))
finally:
    host.location = original
    bpy.context.view_layer.update()
s.frame_set(1)
# For each pair of consecutive samples take the swept XY bounding rectangle.
# Using AABBs for both the eye track and solids understates the true clearance.
near = [
    (bounds(ob), ob.name)
    for ob in solids
    if bounds(ob)[1][2] > 0.01 and bounds(ob)[0][2] < 1.82
]
path_clearance = {}
for label, first, last in [("screen", 217, 313), ("gap", 337, 457)]:
    closest = math.inf
    previous = None
    for f in range(first, last + 1):
        s.frame_set(f)
        x, y, z = s.camera.matrix_world.translation
        assert abs(z - 1.59) < 1e-5
        if previous is not None:
            x0, x1 = sorted((x, previous[0]))
            y0, y1 = sorted((y, previous[1]))
            closest = min(closest, y0 + 2.2, 2.2 - y1, x0 + 14.7 - delta, 14.7 - x1)
            for (lo, hi), name in near:
                dx = max(lo[0] - x1, x0 - hi[0], 0)
                dy = max(lo[1] - y1, y0 - hi[1], 0)
                closest = min(closest, math.hypot(dx, dy))
        previous = (x, y)
    assert closest >= 0.25, (label, closest)
    path_clearance[label] = round(closest, 3)
s.frame_set(1)
# Compare geometric data and transforms, independent of Blender file headers and save paths.
digest = hashlib.sha256()
for o in sorted(s.objects, key=lambda x: x.name):
    digest.update((o.name + "\0" + o.type).encode())
    digest.update(
        struct.pack("<16f", *(round(l, 5) for row in o.matrix_world for l in row))
    )
    if o.type == "MESH":
        for v in o.data.vertices:
            digest.update(struct.pack("<3f", *(round(l, 5) for l in v.co)))
        for f in o.data.polygons:
            digest.update(struct.pack("<" + "I" * len(f.vertices), *f.vertices))
        if o.data.uv_layers:
            for uv in o.data.uv_layers.active.uv:
                digest.update(struct.pack("<2f", *uv.vector))
    if o.type == "CURVE":
        for spline in o.data.splines:
            for v in spline.bezier_points:
                digest.update(
                    struct.pack("<9f", *v.co, *v.handle_left, *v.handle_right)
                )
res = dict(
    blender=bpy.app.version_string,
    seed=s["seed"],
    objects=len(s.objects),
    types=dict(collections.Counter(o.type for o in s.objects)),
    collections={g: len(bpy.data.collections[g].all_objects) for g in groups},
    characters_by_section=[sum(o["section"] == i for o in actors) for i in range(1, 6)],
    characters=len(actors),
    depth_bands=dict(
        sorted(
            collections.Counter(
                str(o["depth_band"]) for o in s.objects if "depth_band" in o
            ).items()
        )
    ),
    relief_triangles=sum(len(o.data.polygons) for o in reliefs),
    materials=sorted(m.name for m in bpy.data.materials if m.users),
    packed_image_bytes=image.packed_file.size,
    dimensions_m=[round(slab.dimensions.x, 2), round(slab.dimensions.y, 2)],
    gap_length_m=gap_length,
    mallets_and_drum_shift_m=shifts,
    walk_clear_radius_lower_bound_m=path_clearance,
    depth_extent_m=round(max(bounds(o)[1][1] for o in solids) - min_y, 3),
    screen_heights_m=[round(v, 3) for v in heights],
    route_clear_width_lower_bound_m=round(min_y + 2.2, 3),
    eye_height_m=1.59,
    screen_sightline_hit=center,
    side_sightline_hit=side,
    figure_furniture_surface_crossings=len(crossings),
    geometry_sha256=digest.hexdigest(),
)
if a.layout:
    layout = {}
    for group in ("Screens", "Furniture", "Characters", "Props", "Lights"):
        for obj in bpy.data.collections[group].all_objects:
            in_farewell = any(
                c.name.startswith(("05 · 散宴", "四 · 留白出口"))
                for c in obj.users_collection
            ) or (group == "Lights" and "散宴" in obj.name)
            if obj.type in ("CURVE", "MESH"):
                extents = bounds(obj)
            else:
                extents = [list(obj.matrix_world.translation)]
            layout[obj.name] = dict(moves=in_farewell, points=extents)
    a.layout.parent.mkdir(parents=True, exist_ok=True)
    a.layout.write_text(json.dumps(layout, ensure_ascii=False))
if a.compare:
    reference = json.loads(a.compare.read_text())
    for key in res:
        if key in ("blender", "screen_sightline_hit") or (
            a.portable and key == "geometry_sha256"
        ):
            continue
        assert res[key] == reference[key], key
if a.report:
    a.report.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(res, ensure_ascii=False))
