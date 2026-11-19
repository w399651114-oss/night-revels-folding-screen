"""Run with Blender --background --factory-startup --python-exit-code 1 --python scripts/build.py -- --out <file>."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
args = argparse.ArgumentParser()
args.add_argument("--out", type=Path, default=ROOT/"scene/night-revels.blend")
args.add_argument("--stage-only", action="store_true")
opt = args.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "夜宴 · 手卷事件空间"
scene.unit_settings.system = "METRIC"
SEED = 963
scene["seed"] = SEED
scene["reading_direction"] = "+X → −X"
def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent else scene.collection.children).link(c)
    return c

C = {s:collection(s) for s in ("Sections","Screens","Furniture","Characters","Props","Lights","GapCorridor","StudyViews")}
events = ["听乐","观舞","暂歇","清吹","散宴"]
zones = [(8.6,14.7),(3.05,8.6),(-1.55,3.05),(-7.05,-1.55),(-14.7,-10.35)]
groups = {s:[collection(f"{i+1:02d} · {e} · {s}",C[s]) for i,e in enumerate(events)] for s in ("Characters","Furniture","Props")}
def empty(c,n,p):
    o=bpy.data.objects.new(n,None); c.objects.link(o); o.location=p; o.empty_display_size=.12; return o

def mesh(c,n,v,f,mat):
    m=bpy.data.meshes.new(n);m.from_pydata(v,[],f);m.update()
    o=bpy.data.objects.new(n,m);c.objects.link(o)
    if mat: m.materials.append(mat)
    return o

def material(n,color,rough=.55,metal=0,grain=None):
    m=bpy.data.materials.new(n);m.diffuse_color=(*color,1);m.use_nodes=True
    nt=m.node_tree;p=nt.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1);p.inputs["Roughness"].default_value=rough;p.inputs["Metallic"].default_value=metal
    if grain:
        tex=nt.nodes.new("ShaderNodeTexCoord"); vec=nt.nodes.new("ShaderNodeVectorMath");vec.operation="MULTIPLY"
        vec.inputs[1].default_value=grain;nt.links.new(tex.outputs["Object"],vec.inputs[0])
        noise=nt.nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=4;nt.links.new(vec.outputs[0],noise.inputs[0])
        ramp=nt.nodes.new("ShaderNodeValToRGB")
        for a,k in zip(ramp.color_ramp.elements,[.56,1.35]):a.color=(*(min(1,x*k) for x in color),1)
        nt.links.new(noise.outputs["Fac"],ramp.inputs[0]);nt.links.new(ramp.outputs[0],p.inputs["Base Color"])
        bump=nt.nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.2;bump.inputs["Distance"].default_value=.0008
        nt.links.new(noise.outputs["Fac"],bump.inputs["Height"]);nt.links.new(bump.outputs[0],p.inputs["Normal"])
    return m

wood=material("紫褐髹木 · 顺纹",(.065,.028,.017),.36,0,(1,15,35))
lac=material("乌漆 · 抛光",(.026,.019,.016),.29,0,(3,11,25))
brass=material("旧铜 · 铰链包角",(.40,.235,.09),.4,.65)
silk=material("素绢 · 暖赭",(.51,.359,.207),.77,0,(75,95,4))
floor=material("深褐绢帛 · 地经纬",(.099,.071,.055),.78,0,(100,165,2))
cel=material("青瓷 · 温润釉面",(.315,.47,.385),.21)
red=material("朱砂漆",(.42,.068,.041),.38,0,(3,3,12))
cream=material("米白锦褥",(.61,.47,.29),.8,0,(80,3,40))
ink=material("墨线",(.019,.016,.015))
bamboo=material("斑竹与丝弦",(.48,.31,.132),.46,0,(25,25,2))
ground=material("绢色虚空",(.40,.30,.20),.96)
def box(c,n,p,size,mat,bevel=.009,rot=0):
    a,b,d=[s/2 for s in size]
    verts=[(x,y,z) for z in (-d,d) for y in (-b,b) for x in (-a,a)]
    o=mesh(c,n,verts,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat);o.location=p;o.rotation_euler.z=rot
    if bevel:
        mod=o.modifiers.new("手磨倒棱","BEVEL");mod.width=min(bevel,a*.45,b*.45,d*.45);mod.segments=3
        o.modifiers.new("面法线","WEIGHTED_NORMAL")
    return o

def lathe(c,n,p,profile,mat,seg=32):
    verts=[];faces=[]
    for r,z in profile:
        for i in range(seg):
            t=math.tau*i/seg;verts.append((max(.0001,r)*math.cos(t),max(.0001,r)*math.sin(t),z))
    for j in range(len(profile)-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;faces.append((a,b,b+seg,a+seg))
    faces.extend([tuple(reversed(range(seg))),tuple(range(len(verts)-seg,len(verts)))])
    o=mesh(c,n,verts,faces,mat);o.location=p
    for f in o.data.polygons[:-2]:f.use_smooth=True
    return o

def rod(c,n,a,b,r,mat,r2=None):
    v=Vector(b)-Vector(a);o=lathe(c,n,a,[(r,0),(r2 if r2 is not None else r,v.length)],mat,16)
    o.rotation_euler=v.to_track_quat("Z","Y").to_euler();return o

def line(c,n,points,r,mat):
    cr=bpy.data.curves.new(n,"CURVE");cr.dimensions="3D";cr.resolution_u=8;cr.bevel_depth=r;cr.bevel_resolution=2
    sp=cr.splines.new("BEZIER");sp.bezier_points.add(len(points)-1)
    for bp,pt in zip(sp.bezier_points,points):
        bp.co=pt;bp.handle_left_type="AUTO";bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(n,cr);c.objects.link(o);cr.materials.append(mat);return o

img=bpy.data.images.load(str(ROOT/"assets/scroll.jpg"))
def painted(n):
    m=material(n,(.48,.35,.22),.9);nt=m.node_tree;p=nt.nodes.get("Principled BSDF")
    tex=nt.nodes.new("ShaderNodeTexImage");tex.image=img;nt.links.new(tex.outputs["Color"],p.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"],p.inputs["Emission Color"]);p.inputs["Emission Strength"].default_value=.23
    return m
paint=painted("宋摹本 · 原卷彩墨 UV")
def uvmap(o,coords):
    uv=o.data.uv_layers.new(name="底本坐标")
    for loop in o.data.loops:
        x,y=coords[loop.vertex_index];uv.data[loop.index].uv=(x/4633,1-y/400)

box(C["Sections"],"长卷基面 · 29.40 × 4.40", (0,0,-.066),(29.4,4.4,.132),floor,.035)
for side in [-1,1]:
    box(C["Sections"],"绢缘 · 缝线",(0,side*2.17,.001),(29.34,.012,.002),bamboo,.0004)
for i,(lo,hi) in enumerate(zones):
    marker=empty(C["Sections"],f"{i+1:02d} {events[i]}",((lo+hi)/2,0,0));marker["x_limits_m"]=[lo,hi]
gap=empty(C["GapCorridor"],"时间间隙 · 3.30 m",(-8.70,0,0));gap["x_limits_m"]=[-10.35,-7.05]
for x in [-10.35,-7.05]:empty(C["GapCorridor"],"留白阈线",(x,-2.2,0))
def screen(name,x,y,widths,angles,landscape=True):
    c=collection(name,C["Screens"])
    for j,(w,deg) in enumerate(zip(widths,angles)):
        a=math.radians(deg);co,si=math.cos(a),math.sin(a)
        def loc(u,v,z):return (x+co*u-si*v,y+si*u+co*v,z)
        def part(n,u,v,z,W,D,H,m):return box(c,n,loc(u,v,z),(W,D,H),m,.006,a)
        for u in (0,w):
            part("立梃",u,0,1.1,.058,.09,2.2,wood)
        for z in [.19,.43,1.965,2.155]:part("攒框横档",w/2,0,z,w,.09,.068,lac)
        part("裱绢板心",w/2,0,1.22,w-.052,.046,1.51,silk)
        for side in [-1,1]:
            v=side*.024
            ob=mesh(c,"屏心 · 山水绢本" if landscape else "屏背 · 素绢", [loc(u,v,z) for u,z in [(.033,.46),(w-.033,.46),(w-.033,1.93),(.033,1.93)]],[(0,1,2,3)],paint if landscape else silk)
            if landscape:
                l=3594+((j%3)*49);uvmap(ob,[(l,126),(l+56,126),(l+56,14),(l,14)])
        for u in [w*k/6 for k in range(1,6)]:
            for z,h in [(.31,.17),(2.065,.12)]:part("透格棂",u,0,z,.012,.024,h,wood)
        for z in [.59,1.68]:
            part("包铜合页",0,-.052,z,.063,.015,.11,brass)
        if j in [0,len(widths)-1]:
            part("抱鼓式屏足",w*.5,0,.065,.34,.48,.13,lac)
        x+=w*co;y+=w*si
screen("一 · 听乐转观舞 · 三折障景",8.60,-.91,[.97,1.03,1.01],[75,108,76])
screen("二 · 观舞转暂歇",3.05,.05,[1.00,.97],[82,103])
screen("三 · 暂歇转清吹 · 独扇座屏",-1.55,.29,[1.48],[85],False)
screen("四 · 留白出口 · 独扇山水",-10.75,.25,[1.57],[94])
box(C["Lights"],"无界绢色承影面",(0,0,-.205),(200,200,.12),ground,.01)
def light(n,kind,p,energy,color,size,target=None):
    d=bpy.data.lights.new(n,kind);d.energy=energy;d.color=color
    if kind=="AREA":d.shape="DISK";d.size=size
    else:d.shadow_soft_size=size
    o=bpy.data.objects.new(n,d);C["Lights"].objects.link(o);o.location=p
    if target:o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
    return o
for i,(lo,hi) in enumerate(zones):
    x=(lo+hi)/2
    light("绢面柔光 "+events[i],"AREA",(x+1,-3.5,5),340,(1,.88,.76),5,(x,0,0))
    light("屏后回光 "+events[i],"AREA",(x-1,3.7,3.6),190,(1,.72,.44),3.4,(x,0,1))
world=bpy.data.worlds.new("远绢色");scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs[0].default_value=(.53,.405,.28,1);world.node_tree.nodes["Background"].inputs[1].default_value=.45
# Fade the light-catching silk field into the same radiance as the sky.
nt=ground.node_tree
geo=nt.nodes.new("ShaderNodeNewGeometry");length=nt.nodes.new("ShaderNodeVectorMath");length.operation="LENGTH"
nt.links.new(geo.outputs["Position"],length.inputs[0])
fade=nt.nodes.new("ShaderNodeMapRange");fade.inputs["From Min"].default_value=17;fade.inputs["From Max"].default_value=55
nt.links.new(length.outputs["Value"],fade.inputs["Value"])
em=nt.nodes.new("ShaderNodeEmission");em.inputs[0].default_value=(.53,.405,.28,1);em.inputs[1].default_value=.45
mix=nt.nodes.new("ShaderNodeMixShader");nt.links.new(fade.outputs[0],mix.inputs[0]);nt.links.new(nt.nodes.get("Principled BSDF").outputs[0],mix.inputs[1]);nt.links.new(em.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes.get("Material Output").inputs[0])
fog=bpy.data.materials.new("烛雾 · 稀薄均质");fog.use_nodes=True;nt=fog.node_tree;nt.nodes.remove(nt.nodes.get("Principled BSDF"))
vol=nt.nodes.new("ShaderNodeVolumeScatter");vol.inputs["Color"].default_value=(.88,.73,.55,1);vol.inputs["Density"].default_value=.0035
nt.links.new(vol.outputs[0],nt.nodes.get("Material Output").inputs["Volume"])
mist=box(C["Lights"],"烛雾场",(0,.4,2),(32,8,4.5),fog,0);mist.display_type="WIRE"
def camera(n,p,t,lens=37,ortho=None):
    d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);C["StudyViews"].objects.link(o);o.location=p
    o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler();d.lens=lens
    if ortho:d.type="ORTHO";d.ortho_scale=ortho
    return o
cam=camera("01 · 展卷总览",(5,-34,14.5),(0,0,.72),ortho=32.8)
camera("02 · 屏前驻足",(10.17,-1.47,1.59),(8.52,.25,1.12),25)
camera("03 · 绕屏见舞",(7.14,-1.62,1.59),(4.82,.38,1.04),27)
camera("04 · 留白间隙",(-6.60,-1.48,1.59),(-11.7,-.08,.80),27)
camera("05 · 听乐近观",(10.65,-5.75,2.15),(11.78,.44,1.00),42)
camera("06 · 清吹合奏",(-5.85,-5.10,1.85),(-4.86,.35,1.05),45)
camera("07 · 案头与围榻",(11.48,-2.08,1.16),(12.12,-.62,.70),46)
scene.camera=cam
if not opt.stage_only:
    exec(compile((ROOT/"scripts/ensemble.py").read_text(), "ensemble.py","exec"))
if not opt.stage_only:
    exec(compile((ROOT/"scripts/textiles.py").read_text(), "textiles.py","exec"))
# Apply the same five depth labels to event props, furniture and painted layers.
bpy.context.view_layer.update()
for group in ("Characters","Props","Furniture"):
    for obj in C[group].all_objects:
        if obj.type=="EMPTY":y=obj.matrix_world.translation.y
        else:y=sum((obj.matrix_world@Vector(pt)).y for pt in obj.bound_box)/8
        obj["depth_band"]=1+sum(y>b for b in (-.89,-.17,.55,1.27))
scene.render.engine="CYCLES";scene.cycles.seed=SEED;scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=730;scene.render.resolution_percentage=100
scene.view_settings.view_transform="AgX";scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
from mathutils import Euler
for area in bpy.context.screen.areas:
    if area.type=="VIEW_3D":
        sp=area.spaces.active;sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
        sp.region_3d.view_distance=24;sp.region_3d.view_location=(0,0,1);sp.region_3d.view_perspective="CAMERA";sp.clip_end=400
        sp.overlay.show_overlays=False;sp.overlay.show_extras=False;sp.shading.color_type="TEXTURE"
for i,c in enumerate(sorted(C["StudyViews"].objects,key=lambda o:o.name)):
    marker=scene.timeline_markers.new(c.name,frame=1+i*24);marker.camera=c
scene.frame_end=145;scene.frame_set(1)
# Factory Shading workspace stores the maker's home as a file-browser path.
for screen_layout in bpy.data.screens:
    for area in screen_layout.areas:
        for space in area.spaces:
            if space.type=="FILE_BROWSER" and space.params:
                space.params.directory=b"/" * max(2,len(space.params.directory))
                space.params.directory=b"//"
bpy.ops.file.pack_all()
img.filepath="//../assets/scroll.jpg"
for source in img.packed_files:source.filepath=img.filepath
opt.out.parent.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(opt.out.resolve()),compress=True)
print("BUILT",len(scene.objects),len(bpy.data.materials),opt.out)
