"""Ensemble, relief meshes and objects. Executed in build.py's scene context."""
from mathutils.geometry import delaunay_2d_cdt

def drape(c,n,x,y,z,w,d,drop,mat):
    vs=[];fs=[];nx,ny=56,20
    for j in range(ny+1):
        v=j/ny
        for i in range(nx+1):
            u=i/nx
            fall=max(0,(.22-v)/.22)
            wrinkle=(.004+.016*fall)*math.sin(u*73+v*2)+.004*math.cos(31*u-5*v)
            vs.append((x+(u-.5)*w,y+(v-.5)*d+fall*wrinkle,z-fall*drop+wrinkle*(1-.55*fall)))
            if i and j:
                k=len(vs)-1;fs.append((k-nx-2,k-nx-1,k,k-1))
    o=mesh(c,n,vs,fs,mat)
    for f in o.data.polygons:f.use_smooth=True
    mod=o.modifiers.new("锦缘厚度","SOLIDIFY");mod.thickness=.004
    return o

def table(c,n,x,y,w,d,h,bed=False):
    box(c,n+" · 面心",(x,y,h-.028),(w,d,.056),lac,.014)
    for yy in (-1,1):
        box(c,n+" · 束腰",(x,y+yy*(d/2-.035),h-.094),(w-.052,.052,.093),wood)
        for zz in [h-.069,h-.133]:
            box(c,n+" · 起线",(x,y+yy*(d/2-.005),zz),(w-.055,.009,.009),brass,.002)
    for xx in (-1,1):
        for yy in (-1,1):
            px=x+xx*(w/2-.075);py=y+yy*(d/2-.065)
            lathe(c,n+" · 旋足",(px,py,0),[(.051,0),(.055,.025),(.037,.061),(.034,h*.35),(.045,h-.11),(.063,h-.08),(.048,h-.052)],wood,24)
            line(c,n+" · 云头牙子",[(px,py,h-.27),(px-xx*.03,py,h-.19),(px-xx*.12,py,h-.15),(px-xx*.17,py,h-.10)],.017,wood)
    if bed:
        drape(c,n+" · 有褶锦褥",x,y-.015,h+.014,w-.055,d-.03,.145,cream)
        for xx in (-1,1):
            px=x+xx*(w/2-.045)
            for yy in [-.23,.44]:
                if abs(yy)<d/2:box(c,n+" · 扶栏柱",(px,y+yy,h+.13),(.045,.045,.27),lac)
            box(c,n+" · 扶手",(px,y+.14,h+.26),(.058,d*.63,.047),wood)
        for yy in [-d/2+.014]:
            for k in range(max(2,int(w/.18))):
                px=x-w/2+.115+k*.18
                line(c,n+" · 卷草牙板",[(px-.056,y+yy,h-.113),(px-.023,y+yy-.006,h-.08),(px+.025,y+yy-.006,h-.104),(px+.049,y+yy,h-.084)],.0055,brass)
    return h

def chair(sec,n,x,y,h=.45):
    y+=.14
    c=groups["Furniture"][sec-1]
    table(c,n,x,y,.57,.52,h)
    for u in [-.25,.25]:
        rod(c,n+" · 靠背柱",(x+u,y+.22,h-.02),(x+u,y+.31,h+.48),.024,wood)
    box(c,n+" · 背板",(x,y+.30,h+.32),(.48,.031,.24),wood,.022)
    box(c,n+" · 搭脑",(x,y+.32,h+.49),(.61,.054,.052),lac,.02)

table(groups["Furniture"][0],"听乐围榻",12.80,1.18,2.38,1.46,.48,True)
table(groups["Furniture"][2],"暂歇床榻",.17,1.08,2.80,1.43,.52,True)
chair(4,"清吹禅椅",-2.61,1.25,.51)
chair(1,"乐伎矮座",9.55,.16,.37)
chair(1,"听者胡床",10.43,.365)
chair(1,"背坐客椅",11.48,-.21)
chair(2,"观舞曲背椅",6.98,-.10)
chair(4,"拍板客椅",-6.48,.59)
chair(5,"散宴独坐椅",-12.07,.33)

table(groups["Furniture"][0],"酒馔长案",12.09,-1.02,1.28,.52,.63)
table(groups["Furniture"][0],"小食案",10.49,-.69,.80,.38,.47)
table(groups["Furniture"][2],"净手小几",1.39,-.62,.71,.46,.54)
table(groups["Furniture"][4],"余席矮几",-13.17,-.56,.83,.49,.46)

people=json.loads((ROOT/"assets/figures.json").read_text())
anchors={}
offsets=[3580,2750,2115,1000,0]
def make_person(rec):
    sec,name=rec["section"],rec["name"];x,y,z,h,yaw=rec["pose"]
    # Partial figures terminate at an overlap in the surviving image.
    if name=="青衣宾客·拱手":z,h=.79,.91
    if name=="小侍·听乐":z,h=.62,.78
    if name=="红衣观者·后倚":x,y=6.98,-.26
    if name=="韩熙载·净手":y=.83
    if name=="郎粲·红袍盘坐":z=.488
    if name=="榻上侍女·一":z,h=.535,.70
    if name.startswith("清吹") and sec==4:
        xx=[p[0]-1000 for p in rec["outline"]]; yy=[p[1] for p in rec["outline"]]
        x=-4.84+((min(xx)+max(xx))*.5-365)*.00605
        y=.10+(298-max(yy))*.007
        h=(max(yy)-min(yy))*.00605
    c=groups["Characters"][sec-1];o=empty(c,name,(x,y,z));o.rotation_euler.z=math.radians(yaw)
    o["role"]="figure";o["section"]=sec;o["evidence"]="L1 正面图像 / H 纵深尺度"
    pts=[Vector(p) for p in rec["outline"]]
    left=min(p.x for p in pts);right=max(p.x for p in pts);top=min(p.y for p in pts);bottom=max(p.y for p in pts)
    center=(left+right)/2;s=h/(bottom-top);span=right-left
    def vertex(px,py):
        u=(px-left)/span;v=(bottom-py)/(bottom-top)
        relief=-.046*max(0,math.sin(math.pi*u))*(.62+.38*math.sin(math.pi*v))-.009*math.sin(13*u+1.3*v)*math.sin(math.pi*v)**2
        return ((px-center)*s,relief,(bottom-py)*s)
    if sum(a.x*b.y-b.x*a.y for a,b in zip(pts,pts[1:]+pts[:1])) < 0:
        pts.reverse()
    count=len(pts)
    for j in range(1,26):
        for i in range(1,13):pts.append(Vector((left+span*i/13,top+(bottom-top)*j/26)))
    result=delaunay_2d_cdt(pts,[],[list(range(count))],1,.00001,True)
    points,_,faces,_,_,orig=result
    faces=[tuple(reversed(face)) for face,ids in zip(faces,orig) if 0 in ids]
    assert len(faces)>20, f"Empty relief surface: {name}"
    used=sorted({idx for face in faces for idx in face})
    remap={old:new for new,old in enumerate(used)}
    points=[points[idx] for idx in used]
    faces=[tuple(remap[idx] for idx in face) for face in faces]
    body=mesh(c,name+" · 彩墨浅浮雕",[vertex(*p) for p in points],faces,paint);body.parent=o
    uvmap(body,points)
    for f in body.data.polygons:f.use_smooth=True
    mod=body.modifiers.new("裱片 · 绢背","SOLIDIFY");mod.thickness=.012;mod.offset=-1
    body.data.materials.append(silk);mod.material_offset=1;mod.material_offset_rim=1
    o["depth_band"]=min(5,max(1,round((y+1.25)/.72)+1))
    def local(px,py,forward=.012):
        q=Vector(vertex(offsets[sec-1]+px,py));q.y-=forward
        return tuple(Vector((x,y,z))+o.rotation_euler.to_matrix()@q)
    anchors[name]=(o,local)
    if name in ("青衣宾客·拱手","小侍·听乐","近屏青衣宾客","持杖随从"):
        # Join the cropped torso to a conjectural garment. Use the bottom of the
        # painted fragment to locate its support instead of centering on its hat.
        low=[p for p in points if p.y > bottom-.09*(bottom-top)]
        cx=(sum(p.x for p in low)/len(low)-center)*s
        dark=material(name+" · 推定下裳",(.079,.068,.048) if "小侍" not in name else (.30,.32,.262),.84,0,(65,80,5))
        vv=[];ff=[];nr=40
        for j in range(14):
            t=j/13
            for k in range(nr):
                angle=math.tau*k/nr
                radius=(.147+.051*(1-t))*(1+.075*math.cos(9*angle+.95*t))
                vv.append((cx+radius*math.cos(angle),.015+radius*.49*math.sin(angle),-z+t*(z+.085)))
                if j:
                    q=(k+1)%nr;ff.append(((j-1)*nr+k,(j-1)*nr+q,j*nr+q,j*nr+k))
        skirt=mesh(c,name+" · 遮压处推定衣摆",vv,ff,dark);skirt.parent=o
        for f in skirt.data.polygons:f.use_smooth=True
        skirt["evidence"]="H 下摆被遮处"
for rec in people:make_person(rec)
for name,(root,_) in anchors.items():
    if name.startswith("清吹"):
        xx,yy,_=root.location
        table(groups["Furniture"][3],"合奏低杌",xx,yy+.39,.34,.43,.32)

bpy.context.view_layer.update()

def regrod(name,n,a,b,r,mat):
    root,at=anchors[name];c=groups["Props"][root["section"]-1]
    ob=rod(c,n,at(*a),at(*b),r,mat);ob["figure"]=name
    # Use parent inverse so editing the event actor also moves its instrument.
    bpy.context.view_layer.update();ob.parent=root;ob.matrix_parent_inverse=root.matrix_world.inverted()
    return ob

def trace_prop(name,n,polygon):
    root,at=anchors[name];c=groups["Props"][root["section"]-1]
    ob=mesh(c,n,[at(x,y,.014) for x,y in polygon],[tuple(range(len(polygon)))],paint)
    uvmap(ob,[(offsets[root["section"]-1]+x,y) for x,y in polygon])
    ob.parent=root;ob.matrix_parent_inverse=root.matrix_world.inverted()
    sol=ob.modifiers.new("器身厚度","SOLIDIFY");sol.thickness=.032
    return ob
pipa="李家明妹·侧坐弹琵琶"
trace_prop(pipa,"曲项琵琶 · 原卷面板",[(54,213),(68,202),(97,201),(122,196),(152,187),(167,175),(176,173),(176,182),(159,198),(146,219),(131,245),(110,259),(81,264),(60,251),(50,233)])
for i in range(4):regrod(pipa,"琵琶丝弦 "+str(i+1),(77,241+i),(168,182+i*.72),.00085,bamboo)
for i in range(4):regrod(pipa,"曲项弦轴",(151+4*i,189-i*3),(148+4*i,185-i*3),.0045,lac)
for name,a,b in [("清吹三·横笛",(373,110),(416,96)),("清吹五·横笛",(494,125),(544,109)),("清吹二·纵管",(305,121),(332,101)),("清吹四·纵管",(425,141),(449,103)),("清吹一·纵管",(245,93),(245,138))]:
    regrod(name,("横笛" if "横笛" in name else "筚篥类纵管")+" · 管身",a,b,.008,bamboo)
    for j in range(6):
        f=.16+.11*j;px=a[0]+(b[0]-a[0])*f;py=a[1]+(b[1]-a[1])*f
        regrod(name,"管孔墨点",(px,py,.020),(px+.27,py+.27,.020),.0028,ink)
for name,a,b in [("执拍板者",(41,187),(97,151)),("拍板乐人",(340,138),(373,105))]:
    for k in range(3):regrod(name,"檀木拍板 "+str(k+1),(a[0]+k,a[1]+k),(b[0]+k,b[1]+k),.009,wood)
# Source leaves the reed classification unresolved. A removable reconstructed sheng sits on a stand.
c=groups["Props"][3];x,y=-3.64,-.72
table(groups["Furniture"][3],"笙匣 · 研究陈列",x,y,.43,.29,.33)
gourd=lathe(c,"笙 · 匏斗", (x,y,.331),[(.04,0),(.084,.02),(.088,.08),(.06,.115)],wood)
gourd["evidence"]="H 器物补型与位置"
for k in range(17):
    a=k*math.tau/17;px=x+.048*math.cos(a);py=y+.048*math.sin(a)
    ht=.17+.18*abs(math.sin(a*1.5));rod(c,"笙簧管 %02d"%(k+1),(px,py,.43),(px,py,.43+ht),.0065,bamboo)
rod(c,"笙吹口",(x-.045,y,.41),(x-.155,y,.475),.013,wood,.008)
c=groups["Props"][1];x,y=6.12,.39
lathe(c,"羯鼓 · 朱漆鼓腔",(x,y,.12),[(.30,0),(.32,.05),(.255,.18),(.225,.42),(.29,.69),(.355,.81),(.35,.87)],red,64)
lathe(c,"羯鼓 · 鼓皮",(x,y,.98),[(.344,0),(.344,.014),(.01,.019)],cream,64)
lathe(c,"羯鼓 · 鼓座",(x,y,0),[(.35,0),(.36,.03),(.285,.08),(.29,.13)],lac)
for j in range(24):
    a=math.tau*j/24;u,v=math.cos(a),math.sin(a)
    rod(c,"鼓边铜钉",(x+.337*u,y+.337*v,.965),(x+.355*u,y+.355*v,.965),.009,brass)
    if j%2==0:line(c,"系革绳",[(x+.30*u,y+.30*v,.19),(x+.256*u,y+.256*v,.58),(x+.34*u,y+.34*v,.938)],.0048,bamboo)
root,at=anchors["韩熙载·击鼓"]
for u,v in [(585,99),(617,140)]:
    rod(c,"击鼓槌",at(u,v,.035),(x+.09+(u-585)*.004,y-.02,1.06),.009,wood,.014)
regrod("韩熙载·持槌送客","散宴手槌",(308,201),(387,150),.008,wood)
def service(sec,x,y,z,n):
    c=groups["Props"][sec-1]
    for i in range(n):
        px=x+(i-(n-1)/2)*.17
        lathe(c,"浅腹盘 · 足与内膛",(px,y,z),[(.026,0),(.032,.009),(.042,.018),(.076,.032),(.078,.039),(.073,.042),(.062,.033),(.031,.018),(.001,.018)],cel,48)
        lathe(c,"酒盏 · 内釉",(px,y+.12,z),[(.018,0),(.019,.009),(.027,.021),(.034,.062),(.033,.065),(.03,.061),(.020,.018),(.001,.015)],cream,36)
        for j in range(3):
            ob=lathe(c,"果实",(px+(j-1)*.021,y+(.012 if j==1 else 0),z+.021),[(.009,0),(.016,.008),(.012,.023),(.002,.027)],red)
service(1,12.09,-1.07,.63,5);service(1,10.49,-.73,.47,3);service(5,-13.17,-.59,.46,3)
for x,y,z in [(11.63,-.89,.63),(-12.87,-.56,.46)]:
    c=groups["Props"][0 if x>0 else 4]
    lathe(c,"执壶 · 圈足梨腹",(x,y,z),[(.035,0),(.048,.015),(.065,.045),(.068,.10),(.041,.15),(.027,.166),(.029,.201),(.038,.207)],cel,48)
    line(c,"执壶提梁",[(x+.049,y,z+.055),(x+.108,y,z+.106),(x+.096,y,z+.167),(x+.029,y,z+.161)],.009,cel)
    rod(c,"执壶流",(x-.047,y,z+.07),(x-.11,y,z+.155),.018,cel,.009)
lathe(groups["Props"][2],"净手盆 · 内外壁",(-.22,.32,.81),[(.082,0),(.097,.016),(.15,.069),(.155,.079),(.147,.081),(.09,.022),(.001,.018)],brass,64)
# Pool of light is offset from the main route.
flame=material("烛芯发光",(.99,.45,.10));p=flame.node_tree.nodes.get("Principled BSDF");p.inputs["Emission Color"].default_value=(1,.34,.065,1);p.inputs["Emission Strength"].default_value=4.0
for i,(lo,hi) in enumerate(zones):
    x=lo+.37;y=1.83;c=groups["Props"][i]
    lathe(c,"灯座",(x,y,0),[(.10,0),(.12,.025),(.05,.063),(.026,.18),(.020,.73),(.065,.76),(.098,.79),(.097,.81)],brass)
    lathe(c,"蜡烛",(x,y,.81),[(.023,0),(.023,.14),(.017,.146)],cream)
    lathe(c,"烛焰",(x,y,.954),[(.006,0),(.013,.014),(.007,.031),(.001,.054)],flame)
    light("烛光 "+events[i],"POINT",(x,y,1.04),14,(1,.45,.14),.09)
