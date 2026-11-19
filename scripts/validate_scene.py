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

p=argparse.ArgumentParser()
p.add_argument("--report",type=Path)
p.add_argument("--compare",type=Path)
a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
s=bpy.context.scene
groups=("Sections","Screens","Furniture","Characters","Props","Lights","GapCorridor","StudyViews")
assert all(bpy.data.collections.get(g) for g in groups)
assert s.unit_settings.system=="METRIC" and s.unit_settings.scale_length==1
assert s["seed"]==s.cycles.seed==963
slab=next(o for o in bpy.data.collections["Sections"].objects if "长卷基面" in o.name)
assert abs(slab.dimensions.x-29.4)<.001 and abs(slab.dimensions.y-4.4)<.001
image=bpy.data.images["scroll.jpg"]
assert image.packed_file and image.size[:]==(13898,1200)
assert all(p.filepath.startswith("//") for p in image.packed_files)
graph=bpy.context.evaluated_depsgraph_get()
from functools import lru_cache
@lru_cache(None)
def bounds(o):
    ob=o.evaluated_get(graph); m=ob.to_mesh(); v=[ob.matrix_world@p.co for p in m.vertices];ob.to_mesh_clear()
    return [min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]
solids=[o for group in ("Screens","Furniture","Props","Characters") for o in bpy.data.collections[group].all_objects if o.type in ("MESH","CURVE")]
min_y=100
for o in solids:
    lo,hi=bounds(o)
    assert lo[0]>=-14.701 and hi[0]<=14.701, (o.name,"stage X",lo,hi)
    assert lo[2]>=-.008,(o.name,"floor",lo)
    assert hi[0]<=-10.35 or lo[0]>=-7.05,(o.name,"gap occupied",lo,hi)
    if hi[2]>.01 and lo[2]<1.82:min_y=min(min_y,lo[1])
assert min_y-(-2.2)>.60,min_y
panels=list(bpy.data.collections["Screens"].children)
heights=[max(bounds(o)[1][2] for o in c.objects) for c in panels]
assert all(abs(h-2.2)<.001 for h in heights)
trees=[]
for o in bpy.data.collections["Screens"].all_objects:
    if o.type=="MESH":trees.append((o,BVHTree.FromObject(o,graph)))
def ray(x,y,z,end):
    origin=Vector((x,y,z));direction=Vector((-1,0,0));hits=[]
    for ob,tree in trees:
        inv=ob.matrix_world.inverted()
        pos,_,_,dist=tree.ray_cast(inv@origin,inv.to_3x3()@direction,x-end)
        if pos is not None:hits.append((round(dist,4),ob.name))
    return min(hits) if hits else None
center=ray(9.6,.45,1.59,7.65);side=ray(9.6,-1.70,1.59,7.65)
assert center and side is None,(center,side)
assert all(ray(9.6,y,1.59,7.65) for y in [-.40,.45,1.25])
actors=[o for o in s.objects if o.get("role")=="figure"]
reliefs=[next(ch for ch in o.children if "彩墨浅浮雕" in ch.name) for o in actors]
for o in reliefs:
    assert len(o.data.polygons)>80 and o.data.uv_layers and o.data.materials[0].name.startswith("宋摹本")
assert len({o["section"] for o in actors if "韩熙载" in o.name})==5
assert len([o for o in actors if o.name.startswith("清吹")])==5
def world_tree(o):
    ob=o.evaluated_get(graph);mesh=ob.to_mesh()
    tree=BVHTree.FromPolygons([ob.matrix_world@v.co for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons])
    ob.to_mesh_clear()
    return tree
furnishings=[(o,world_tree(o)) for o in bpy.data.collections["Furniture"].all_objects if o.type in ("MESH","CURVE")]
crossings=[]
for o in reliefs:
    tree=world_tree(o)
    for f,ft in furnishings:
        if tree.overlap(ft):crossings.append((o.name,f.name))
assert not crossings,crossings
assert len(bpy.data.cameras)==len(s.timeline_markers)==7
# Compare geometric data and transforms, independent of Blender file headers and save paths.
digest=hashlib.sha256()
for o in sorted(s.objects,key=lambda x:x.name):
    digest.update((o.name+'\0'+o.type).encode())
    digest.update(struct.pack("<16f",*(round(l,5) for row in o.matrix_world for l in row)))
    if o.type=="MESH":
        for v in o.data.vertices:digest.update(struct.pack("<3f",*(round(l,5) for l in v.co)))
        for f in o.data.polygons:digest.update(struct.pack("<"+"I"*len(f.vertices),*f.vertices))
        if o.data.uv_layers:
            for uv in o.data.uv_layers.active.uv:digest.update(struct.pack("<2f",*uv.vector))
    if o.type=="CURVE":
        for spline in o.data.splines:
            for v in spline.bezier_points:digest.update(struct.pack("<9f",*v.co,*v.handle_left,*v.handle_right))
res=dict(blender=bpy.app.version_string,seed=s["seed"],objects=len(s.objects),types=dict(collections.Counter(o.type for o in s.objects)),
         collections={g:len(bpy.data.collections[g].all_objects) for g in groups},
         characters_by_section=[sum(o["section"]==i for o in actors) for i in range(1,6)],characters=len(actors),
         depth_bands=dict(sorted(collections.Counter(str(o["depth_band"]) for o in s.objects if "depth_band" in o).items())),
         relief_triangles=sum(len(o.data.polygons) for o in reliefs),
         materials=sorted(m.name for m in bpy.data.materials if m.users),
         packed_image_bytes=image.packed_file.size,
         dimensions_m=[29.4,4.4],gap_length_m=3.30,
         depth_extent_m=round(max(bounds(o)[1][1] for o in solids)-min_y,3),
         screen_heights_m=[round(v,3) for v in heights],
         route_clear_width_lower_bound_m=round(min_y+2.2,3),
         eye_height_m=1.59,screen_sightline_hit=center,side_sightline_hit=side,
         figure_furniture_surface_crossings=len(crossings),
         geometry_sha256=digest.hexdigest())
if a.compare:
    reference=json.loads(a.compare.read_text())
    for key in res:
        if key in ("blender","screen_sightline_hit"):continue
        assert res[key]==reference[key],key
if a.report:a.report.write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(res,ensure_ascii=False))
