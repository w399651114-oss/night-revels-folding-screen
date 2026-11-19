"""Woven selvedges and bed fittings, sectional drapery without enclosing the stage."""

teal = material("石绿经锦", (0.085, 0.205, 0.176), 0.77, 0, (65, 90, 3))
mulberry = material("绛红绫", (0.30, 0.040, 0.030), 0.65, 0, (72, 96, 2))


def weave(m):
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    signals = []
    for direction, freq in [("X", 165), ("Y", 125)]:
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = direction
        wave.inputs["Scale"].default_value = freq
        wave.inputs["Distortion"].default_value = 0.38
        nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
        signals.append(wave.outputs["Fac"])
    cross = nt.nodes.new("ShaderNodeMath")
    cross.operation = "MULTIPLY"
    for i, sig in enumerate(signals):
        nt.links.new(sig, cross.inputs[i])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.00035
    bump.inputs["Strength"].default_value = 0.27
    nt.links.new(cross.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], p.inputs["Normal"])
    p.inputs["Sheen Weight"].default_value = 0.23


for m in (floor, silk, cream, teal, mulberry):
    weave(m)
for sec, x, y, w, d, h in [
    (1, 12.80, 1.18, 2.38, 1.46, 0.48),
    (3, 0.17, 1.08, 2.8, 1.43, 0.52),
]:
    c = groups["Furniture"][sec - 1]
    back = y + d * 0.5 - 0.035
    for xx in [x - w * 0.5 + 0.035, x + w * 0.5 - 0.035]:
        box(c, "围榻端柱", (xx, back, (1.65 + h) / 2), (0.074, 0.078, 1.65 - h), lac)
        lathe(
            c,
            "攒顶柱头",
            (xx, back, 1.65),
            [(0.036, 0), (0.044, 0.017), (0.030, 0.046), (0.014, 0.058)],
            wood,
        )
    for z in [h + 0.12, h + 0.37, 1.53]:
        box(c, "围榻横枨", (x, back, z), (w, 0.064, 0.058), lac)
    box(c, "围榻后屏心", (x, back, 1.00), (w - 0.12, 0.034, 0.99), wood)
    for i in range(3):
        px = x + (i - 1) * (w - 0.18) / 3
        box(
            c,
            "绢绘围子 · 框内",
            (px, back - 0.024, 1.19),
            ((w - 0.26) / 3, 0.017, 0.55),
            silk,
        )
        for z in [0.90, 1.48]:
            box(
                c,
                "嵌线",
                (px, back - 0.038, z),
                ((w - 0.19) / 3, 0.008, 0.009),
                brass,
                0.002,
            )
    # A bed curtain and tie at the outer end. Its short rail belongs to the bed.
    px = x + w / 2 - 0.045
    for yy in [back, back - 0.59]:
        rod(c, "床端帐杆", (px, yy, h), (px, yy, 1.94), 0.022, lac)
    rod(c, "床端短帐棍", (px, back - 0.64, 1.92), (px, back + 0.045, 1.92), 0.021, wood)
    vs = []
    fs = []
    nx, ny = 36, 52
    for j in range(ny + 1):
        v = j / ny
        gather = math.exp(-(((v - 0.49) / 0.17) ** 2))
        for i in range(nx + 1):
            u = i / nx
            yy = back - 0.61 + u * 0.62 + gather * (0.55 - u * 0.53)
            xx = px + 0.047 * math.sin(u * math.tau * 6 + 0.32 * v) * (
                1 - 0.60 * gather
            )
            zz = 0.49 + v * 1.42 + (0.012 * math.cos(u * 38) if j == 0 else 0)
            vs.append((xx, yy, zz))
            if i and j:
                k = len(vs) - 1
                fs.append((k - nx - 2, k - nx - 1, k, k - 1))
    cloth = mesh(c, "束腰垂帐 · 褶面", vs, fs, mulberry if sec == 1 else teal)
    for f in cloth.data.polygons:
        f.use_smooth = True
    sol = cloth.modifiers.new("双层绫", "SOLIDIFY")
    sol.thickness = 0.003
    line(
        c,
        "帐系垂结",
        [
            (px + 0.04, back - 0.03, 1.19),
            (px + 0.055, back - 0.10, 1.10),
            (px + 0.07, back - 0.09, 0.93),
        ],
        0.009,
        bamboo,
    )
for i, (lo, hi) in enumerate(zones):
    for sign in [-1, 1]:
        box(
            C["Sections"],
            "绢沿 · 段内双绦",
            ((lo + hi) / 2, sign * 2.107, 0.002),
            (hi - lo - 0.16, 0.033, 0.003),
            mulberry if i % 2 == 0 else teal,
            0.001,
        )
for x in [gap_exit - 0.004, gap_entry + 0.004]:
    box(
        C["GapCorridor"], "素绢接缝", (x, 0, 0.0015), (0.006, 4.30, 0.003), silk, 0.0006
    )
# Bed-seated reliefs meet the locally undulating cushion instead of an ideal plane.
from mathutils.bvhtree import BVHTree

bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
for name, (actor, _) in anchors.items():
    if actor.location.z <= 0 or any("推定衣摆" in ch.name for ch in actor.children):
        continue
    sec = actor["section"]
    if sec in (1, 3):
        surface = next(
            o for o in groups["Furniture"][sec - 1].objects if "有褶锦褥" in o.name
        )
    elif sec == 4:
        surface = next(
            o for o in groups["Furniture"][3].objects if "清吹禅椅 · 面心" == o.name
        )
    else:
        continue
    ev = surface.evaluated_get(deps)
    sm = ev.to_mesh()
    tree = BVHTree.FromPolygons(
        [ev.matrix_world @ v.co for v in sm.vertices],
        [f.vertices[:] for f in sm.polygons],
    )
    ev.to_mesh_clear()
    body = next(ch for ch in actor.children if "彩墨浅浮雕" in ch.name)
    gaps = []
    shaped = body.evaluated_get(deps)
    shape = shaped.to_mesh()
    for v in shape.vertices:
        pt = shaped.matrix_world @ v.co
        if pt.z > actor.location.z + 0.065:
            continue
        hit, _, _, _ = tree.ray_cast((pt.x, pt.y, pt.z + 0.25), (0, 0, -1), 0.55)
        if hit is not None:
            gaps.append(pt.z - hit.z)
    shaped.to_mesh_clear()
    if gaps:
        actor.location.z += 0.0004 - min(gaps)
        # Tiny undulations can contact a triangle between its vertices.
        for step in range(24):
            bpy.context.view_layer.update()
            shaped = body.evaluated_get(deps)
            shape = shaped.to_mesh()
            probe = BVHTree.FromPolygons(
                [shaped.matrix_world @ v.co for v in shape.vertices],
                [f.vertices[:] for f in shape.polygons],
            )
            shaped.to_mesh_clear()
            if not probe.overlap(tree):
                break
            actor.location.z += 0.0005
        else:
            raise RuntimeError("Unresolved support: " + name)
        actor["support"] = surface.name
    else:
        raise RuntimeError("No support under painted fragment: " + name)
