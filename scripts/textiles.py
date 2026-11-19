"""Woven selvedges and bed fittings, sectional drapery without enclosing the stage."""
teal=material("石绿经锦",(.085,.205,.176),.77,0,(65,90,3))
mulberry=material("绛红绫",(.30,.040,.030),.65,0,(72,96,2))
def weave(m):
    nt=m.node_tree;p=nt.nodes.get("Principled BSDF");coord=nt.nodes.new("ShaderNodeTexCoord")
    signals=[]
    for direction,freq in [("X",165),("Y",125)]:
        wave=nt.nodes.new("ShaderNodeTexWave");wave.wave_type="BANDS";wave.bands_direction=direction
        wave.inputs["Scale"].default_value=freq;wave.inputs["Distortion"].default_value=.38
        nt.links.new(coord.outputs["Object"],wave.inputs["Vector"]);signals.append(wave.outputs["Fac"])
    cross=nt.nodes.new("ShaderNodeMath");cross.operation="MULTIPLY"
    for i,sig in enumerate(signals):nt.links.new(sig,cross.inputs[i])
    bump=nt.nodes.new("ShaderNodeBump");bump.inputs["Distance"].default_value=.00035;bump.inputs["Strength"].default_value=.27
    nt.links.new(cross.outputs[0],bump.inputs["Height"]);nt.links.new(bump.outputs[0],p.inputs["Normal"])
    p.inputs["Sheen Weight"].default_value=.23
for m in (floor,silk,cream,teal,mulberry):weave(m)
for sec,x,y,w,d,h in [(1,12.80,1.18,2.38,1.46,.48),(3,.17,1.08,2.8,1.43,.52)]:
    c=groups["Furniture"][sec-1]
    back=y+d*.5-.035
    for xx in [x-w*.5+.035,x+w*.5-.035]:
        box(c,"围榻端柱",(xx,back,(1.65+h)/2),(.074,.078,1.65-h),lac)
        lathe(c,"攒顶柱头",(xx,back,1.65),[(.036,0),(.044,.017),(.030,.046),(.014,.058)],wood)
    for z in [h+.12,h+.37,1.53]:box(c,"围榻横枨",(x,back,z),(w,.064,.058),lac)
    box(c,"围榻后屏心",(x,back,1.00),(w-.12,.034,.99),wood)
    for i in range(3):
        px=x+(i-1)*(w-.18)/3
        box(c,"绢绘围子 · 框内",(px,back-.024,1.19),((w-.26)/3,.017,.55),silk)
        for z in [.90,1.48]:box(c,"嵌线",(px,back-.038,z),((w-.19)/3,.008,.009),brass,.002)
    # A bed curtain and tie at the outer end. Its short rail belongs to the bed.
    px=x+w/2-.045
    for yy in [back,back-.59]:rod(c,"床端帐杆",(px,yy,h),(px,yy,1.94),.022,lac)
    rod(c,"床端短帐棍",(px,back-.64,1.92),(px,back+.045,1.92),.021,wood)
    vs=[];fs=[];nx,ny=36,52
    for j in range(ny+1):
        v=j/ny;gather=math.exp(-((v-.49)/.17)**2)
        for i in range(nx+1):
            u=i/nx
            yy=back-.61+u*.62+gather*(.55-u*.53)
            xx=px+.047*math.sin(u*math.tau*6+.32*v)*(1-.60*gather)
            zz=.49+v*1.42+(.012*math.cos(u*38) if j==0 else 0)
            vs.append((xx,yy,zz))
            if i and j:
                k=len(vs)-1;fs.append((k-nx-2,k-nx-1,k,k-1))
    cloth=mesh(c,"束腰垂帐 · 褶面",vs,fs,mulberry if sec==1 else teal)
    for f in cloth.data.polygons:f.use_smooth=True
    sol=cloth.modifiers.new("双层绫","SOLIDIFY");sol.thickness=.003
    line(c,"帐系垂结",[(px+.04,back-.03,1.19),(px+.055,back-.10,1.10),(px+.07,back-.09,.93)],.009,bamboo)
for i,(lo,hi) in enumerate(zones):
    for sign in [-1,1]:
        box(C["Sections"],"绢沿 · 段内双绦",((lo+hi)/2,sign*2.107,.002),(hi-lo-.16,.033,.003),mulberry if i%2==0 else teal,.001)
for x in [-10.354,-7.046]:
    box(C["GapCorridor"],"素绢接缝",(x,0,.0015),(.006,4.30,.003),silk,.0006)
# Bed-seated reliefs meet the locally undulating cushion instead of an ideal plane.
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
for name,(actor,_) in anchors.items():
    if actor.location.z<=0 or any("推定衣摆" in ch.name for ch in actor.children):continue
    sec=actor["section"]
    if sec in (1,3):
        surface=next(o for o in groups["Furniture"][sec-1].objects if "有褶锦褥" in o.name)
    elif sec==4:surface=next(o for o in groups["Furniture"][3].objects if "清吹禅椅 · 面心"==o.name)
    else:continue
    ev=surface.evaluated_get(deps);sm=ev.to_mesh()
    tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in sm.vertices],[f.vertices[:] for f in sm.polygons])
    ev.to_mesh_clear()
    body=next(ch for ch in actor.children if "彩墨浅浮雕" in ch.name)
    gaps=[]
    shaped=body.evaluated_get(deps);shape=shaped.to_mesh()
    for v in shape.vertices:
        pt=shaped.matrix_world@v.co
        if pt.z>actor.location.z+.065:continue
        hit,_,_,_=tree.ray_cast((pt.x,pt.y,pt.z+.25),(0,0,-1),.55)
        if hit is not None:gaps.append(pt.z-hit.z)
    shaped.to_mesh_clear()
    if gaps:
        actor.location.z+=.0004-min(gaps)
        # Tiny undulations can contact a triangle between its vertices.
        for step in range(24):
            bpy.context.view_layer.update()
            shaped=body.evaluated_get(deps);shape=shaped.to_mesh()
            probe=BVHTree.FromPolygons([shaped.matrix_world@v.co for v in shape.vertices],[f.vertices[:] for f in shape.polygons])
            shaped.to_mesh_clear()
            if not probe.overlap(tree):break
            actor.location.z+=.0005
        else:raise RuntimeError("Unresolved support: "+name)
        actor["support"]=surface.name
    else:raise RuntimeError("No support under painted fragment: "+name)
