"""Ensemble, relief meshes and objects. Executed in build.py's scene context."""

from mathutils.geometry import delaunay_2d_cdt


def drape(c, n, x, y, z, w, d, drop, mat):
    vs = []
    fs = []
    nx, ny = 56, 20
    for j in range(ny + 1):
        v = j / ny
        for i in range(nx + 1):
            u = i / nx
            fall = max(0, (0.22 - v) / 0.22)
            wrinkle = (0.004 + 0.016 * fall) * math.sin(
                u * 73 + v * 2
            ) + 0.004 * math.cos(31 * u - 5 * v)
            vs.append(
                (
                    x + (u - 0.5) * w,
                    y + (v - 0.5) * d + fall * wrinkle,
                    z - fall * drop + wrinkle * (1 - 0.55 * fall),
                )
            )
            if i and j:
                k = len(vs) - 1
                fs.append((k - nx - 2, k - nx - 1, k, k - 1))
    o = mesh(c, n, vs, fs, mat)
    for f in o.data.polygons:
        f.use_smooth = True
    mod = o.modifiers.new("锦缘厚度", "SOLIDIFY")
    mod.thickness = 0.004
    return o


def table(c, n, x, y, w, d, h, bed=False):
    box(c, n + " · 面心", (x, y, h - 0.028), (w, d, 0.056), lac, 0.014)
    for yy in (-1, 1):
        box(
            c,
            n + " · 束腰",
            (x, y + yy * (d / 2 - 0.035), h - 0.094),
            (w - 0.052, 0.052, 0.093),
            wood,
        )
        for zz in [h - 0.069, h - 0.133]:
            box(
                c,
                n + " · 起线",
                (x, y + yy * (d / 2 - 0.005), zz),
                (w - 0.055, 0.009, 0.009),
                brass,
                0.002,
            )
    for xx in (-1, 1):
        for yy in (-1, 1):
            px = x + xx * (w / 2 - 0.075)
            py = y + yy * (d / 2 - 0.065)
            lathe(
                c,
                n + " · 旋足",
                (px, py, 0),
                [
                    (0.051, 0),
                    (0.055, 0.025),
                    (0.037, 0.061),
                    (0.034, h * 0.35),
                    (0.045, h - 0.11),
                    (0.063, h - 0.08),
                    (0.048, h - 0.052),
                ],
                wood,
                24,
            )
            line(
                c,
                n + " · 云头牙子",
                [
                    (px, py, h - 0.27),
                    (px - xx * 0.03, py, h - 0.19),
                    (px - xx * 0.12, py, h - 0.15),
                    (px - xx * 0.17, py, h - 0.10),
                ],
                0.017,
                wood,
            )
    if bed:
        drape(
            c,
            n + " · 有褶锦褥",
            x,
            y - 0.015,
            h + 0.014,
            w - 0.055,
            d - 0.03,
            0.145,
            cream,
        )
        for xx in (-1, 1):
            px = x + xx * (w / 2 - 0.045)
            for yy in [-0.23, 0.44]:
                if abs(yy) < d / 2:
                    box(
                        c,
                        n + " · 扶栏柱",
                        (px, y + yy, h + 0.13),
                        (0.045, 0.045, 0.27),
                        lac,
                    )
            box(
                c,
                n + " · 扶手",
                (px, y + 0.14, h + 0.26),
                (0.058, d * 0.63, 0.047),
                wood,
            )
        for yy in [-d / 2 + 0.014]:
            for k in range(max(2, int(w / 0.18))):
                px = x - w / 2 + 0.115 + k * 0.18
                line(
                    c,
                    n + " · 卷草牙板",
                    [
                        (px - 0.056, y + yy, h - 0.113),
                        (px - 0.023, y + yy - 0.006, h - 0.08),
                        (px + 0.025, y + yy - 0.006, h - 0.104),
                        (px + 0.049, y + yy, h - 0.084),
                    ],
                    0.0055,
                    brass,
                )
    return h


def chair(sec, n, x, y, h=0.45):
    y += 0.14
    c = groups["Furniture"][sec - 1]
    table(c, n, x, y, 0.57, 0.52, h)
    for u in [-0.25, 0.25]:
        rod(
            c,
            n + " · 靠背柱",
            (x + u, y + 0.22, h - 0.02),
            (x + u, y + 0.31, h + 0.48),
            0.024,
            wood,
        )
    box(c, n + " · 背板", (x, y + 0.30, h + 0.32), (0.48, 0.031, 0.24), wood, 0.022)
    box(c, n + " · 搭脑", (x, y + 0.32, h + 0.49), (0.61, 0.054, 0.052), lac, 0.02)


table(groups["Furniture"][0], "听乐围榻", 12.80, 1.18, 2.38, 1.46, 0.48, True)
table(groups["Furniture"][2], "暂歇床榻", 0.17, 1.08, 2.80, 1.43, 0.52, True)
chair(4, "清吹禅椅", -2.61, 1.25, 0.51)
chair(1, "乐伎矮座", 9.55, 0.16, 0.37)
chair(1, "听者胡床", 10.43, 0.365)
chair(1, "背坐客椅", 11.48, -0.21)
chair(2, "观舞曲背椅", 6.98, -0.10)
chair(4, "拍板客椅", -6.48, 0.59)
chair(5, "散宴独坐椅", -12.07, 0.33)

table(groups["Furniture"][0], "酒馔长案", 12.09, -1.02, 1.28, 0.52, 0.63)
table(groups["Furniture"][0], "小食案", 10.49, -0.69, 0.80, 0.38, 0.47)
table(groups["Furniture"][2], "净手小几", 1.39, -0.62, 0.71, 0.46, 0.54)
table(groups["Furniture"][4], "余席矮几", -13.17, -0.56, 0.83, 0.49, 0.46)

people = json.loads((ROOT / "assets/figures.json").read_text())
figure_ids = json.loads((ROOT / "assets/figure-ids.json").read_text())
anchors = {}
offsets = [3580, 2750, 2115, 1000, 0]


def make_person(rec):
    sec, name = rec["section"], rec["name"]
    x, y, z, h, yaw = rec["pose"]
    # Partial figures terminate at an overlap in the surviving image.
    if name == "青衣宾客·拱手":
        z, h = 0.79, 0.91
    if name == "小侍·听乐":
        z, h = 0.62, 0.78
    if name == "红衣观者·后倚":
        x, y = 6.98, -0.26
    if name == "韩熙载·净手":
        y = 0.83
    if name == "郎粲·红袍盘坐":
        z = 0.488
    if name == "榻上侍女·一":
        z, h = 0.535, 0.70
    if name.startswith("清吹") and sec == 4:
        xx = [p[0] - 1000 for p in rec["outline"]]
        yy = [p[1] for p in rec["outline"]]
        x = -4.84 + ((min(xx) + max(xx)) * 0.5 - 365) * 0.00605
        y = 0.10 + (298 - max(yy)) * 0.007
        h = (max(yy) - min(yy)) * 0.00605
    c = groups["Characters"][sec - 1]
    o = empty(c, name, (x, y, z))
    o.rotation_euler.z = math.radians(yaw)
    o["role"] = "figure"
    o["section"] = sec
    o["source_id"] = figure_ids[name]
    o["evidence"] = "L1 正面图像 / H 纵深尺度"
    pts = [Vector(p) for p in rec["outline"]]
    left = min(p.x for p in pts)
    right = max(p.x for p in pts)
    top = min(p.y for p in pts)
    bottom = max(p.y for p in pts)
    center = (left + right) / 2
    s = h / (bottom - top)
    span = right - left

    def vertex(px, py):
        u = (px - left) / span
        v = (bottom - py) / (bottom - top)
        relief = (
            -0.046
            * max(0, math.sin(math.pi * u))
            * (0.62 + 0.38 * math.sin(math.pi * v))
            - 0.009 * math.sin(13 * u + 1.3 * v) * math.sin(math.pi * v) ** 2
        )
        return ((px - center) * s, relief, (bottom - py) * s)

    if sum(a.x * b.y - b.x * a.y for a, b in zip(pts, pts[1:] + pts[:1])) < 0:
        pts.reverse()
    count = len(pts)
    for j in range(1, 26):
        for i in range(1, 13):
            pts.append(Vector((left + span * i / 13, top + (bottom - top) * j / 26)))
    result = delaunay_2d_cdt(pts, [], [list(range(count))], 1, 0.00001, True)
    points, _, faces, _, _, orig = result
    faces = [tuple(reversed(face)) for face, ids in zip(faces, orig) if 0 in ids]
    assert len(faces) > 20, f"Empty relief surface: {name}"
    used = sorted({idx for face in faces for idx in face})
    remap = {old: new for new, old in enumerate(used)}
    points = [points[idx] for idx in used]
    faces = [tuple(remap[idx] for idx in face) for face in faces]
    body = mesh(c, name + " · 彩墨浅浮雕", [vertex(*p) for p in points], faces, paint)
    body.parent = o
    body["source_id"] = figure_ids[name]
    uvmap(body, points)
    for f in body.data.polygons:
        f.use_smooth = True
    mod = body.modifiers.new("裱片 · 绢背", "SOLIDIFY")
    mod.thickness = 0.012
    mod.offset = -1
    body.data.materials.append(silk)
    mod.material_offset = 1
    mod.material_offset_rim = 1
    o["depth_band"] = min(5, max(1, round((y + 1.25) / 0.72) + 1))

    def local(px, py, forward=0.012):
        q = Vector(vertex(offsets[sec - 1] + px, py))
        q.y -= forward
        return tuple(Vector((x, y, z)) + o.rotation_euler.to_matrix() @ q)

    anchors[name] = (o, local)
    if name in ("青衣宾客·拱手", "小侍·听乐", "近屏青衣宾客", "持杖随从"):
        # Join the cropped torso to a conjectural garment. Use the bottom of the
        # painted fragment to locate its support instead of centering on its hat.
        low = [p for p in points if p.y > bottom - 0.09 * (bottom - top)]
        cx = (sum(p.x for p in low) / len(low) - center) * s
        dark = material(
            name + " · 推定下裳",
            (0.079, 0.068, 0.048) if "小侍" not in name else (0.30, 0.32, 0.262),
            0.84,
            0,
            (65, 80, 5),
        )
        vv = []
        ff = []
        nr = 40
        for j in range(14):
            t = j / 13
            for k in range(nr):
                angle = math.tau * k / nr
                radius = (0.147 + 0.051 * (1 - t)) * (
                    1 + 0.075 * math.cos(9 * angle + 0.95 * t)
                )
                vv.append(
                    (
                        cx + radius * math.cos(angle),
                        0.015 + radius * 0.49 * math.sin(angle),
                        -z + t * (z + 0.085),
                    )
                )
                if j:
                    q = (k + 1) % nr
                    ff.append(
                        ((j - 1) * nr + k, (j - 1) * nr + q, j * nr + q, j * nr + k)
                    )
        skirt = mesh(c, name + " · 遮压处推定衣摆", vv, ff, dark)
        skirt.parent = o
        for f in skirt.data.polygons:
            f.use_smooth = True
        skirt["evidence"] = "H 下摆被遮处"


for rec in people:
    make_person(rec)
for name, (root, _) in anchors.items():
    if name.startswith("清吹"):
        xx, yy, _ = root.location
        table(groups["Furniture"][3], "合奏低杌", xx, yy + 0.39, 0.34, 0.43, 0.32)

bpy.context.view_layer.update()


def regrod(name, n, a, b, r, mat):
    root, at = anchors[name]
    c = groups["Props"][root["section"] - 1]
    ob = rod(c, n, at(*a), at(*b), r, mat)
    ob["figure"] = name
    # Use parent inverse so editing the event actor also moves its instrument.
    bpy.context.view_layer.update()
    ob.parent = root
    ob.matrix_parent_inverse = root.matrix_world.inverted()
    return ob


def trace_prop(name, n, polygon):
    root, at = anchors[name]
    c = groups["Props"][root["section"] - 1]
    ob = mesh(
        c, n, [at(x, y, 0.014) for x, y in polygon], [tuple(range(len(polygon)))], paint
    )
    uvmap(ob, [(offsets[root["section"] - 1] + x, y) for x, y in polygon])
    ob.parent = root
    ob.matrix_parent_inverse = root.matrix_world.inverted()
    sol = ob.modifiers.new("器身厚度", "SOLIDIFY")
    sol.thickness = 0.032
    return ob


pipa = "李家明妹·侧坐弹琵琶"
trace_prop(
    pipa,
    "曲项琵琶 · 原卷面板",
    [
        (54, 213),
        (68, 202),
        (97, 201),
        (122, 196),
        (152, 187),
        (167, 175),
        (176, 173),
        (176, 182),
        (159, 198),
        (146, 219),
        (131, 245),
        (110, 259),
        (81, 264),
        (60, 251),
        (50, 233),
    ],
)
for i in range(4):
    regrod(
        pipa,
        "琵琶丝弦 " + str(i + 1),
        (77, 241 + i),
        (168, 182 + i * 0.72),
        0.00085,
        bamboo,
    )
for i in range(4):
    regrod(
        pipa,
        "曲项弦轴",
        (151 + 4 * i, 189 - i * 3),
        (148 + 4 * i, 185 - i * 3),
        0.0045,
        lac,
    )
for name, a, b in [
    ("清吹三·横笛", (373, 110), (416, 96)),
    ("清吹五·横笛", (494, 125), (544, 109)),
    ("清吹二·纵管", (305, 121), (332, 101)),
    ("清吹四·纵管", (425, 141), (449, 103)),
    ("清吹一·纵管", (245, 93), (245, 138)),
]:
    regrod(
        name,
        ("横笛" if "横笛" in name else "筚篥类纵管") + " · 管身",
        a,
        b,
        0.008,
        bamboo,
    )
    for j in range(6):
        f = 0.16 + 0.11 * j
        px = a[0] + (b[0] - a[0]) * f
        py = a[1] + (b[1] - a[1]) * f
        regrod(
            name,
            "管孔墨点",
            (px, py, 0.020),
            (px + 0.27, py + 0.27, 0.020),
            0.0028,
            ink,
        )
for name, a, b in [
    ("执拍板者", (41, 187), (97, 151)),
    ("拍板乐人", (340, 138), (373, 105)),
]:
    for k in range(3):
        regrod(
            name,
            "檀木拍板 " + str(k + 1),
            (a[0] + k, a[1] + k),
            (b[0] + k, b[1] + k),
            0.009,
            wood,
        )
# Source leaves the reed classification unresolved. A removable reconstructed sheng sits on a stand.
c = groups["Props"][3]
x, y = -3.64, -0.72
table(groups["Furniture"][3], "笙匣 · 研究陈列", x, y, 0.43, 0.29, 0.33)
gourd = lathe(
    c,
    "笙 · 匏斗",
    (x, y, 0.331),
    [(0.04, 0), (0.084, 0.02), (0.088, 0.08), (0.06, 0.115)],
    wood,
)
gourd["evidence"] = "H 器物补型与位置"
for k in range(17):
    a = k * math.tau / 17
    px = x + 0.048 * math.cos(a)
    py = y + 0.048 * math.sin(a)
    ht = 0.17 + 0.18 * abs(math.sin(a * 1.5))
    rod(c, "笙簧管 %02d" % (k + 1), (px, py, 0.43), (px, py, 0.43 + ht), 0.0065, bamboo)
rod(c, "笙吹口", (x - 0.045, y, 0.41), (x - 0.155, y, 0.475), 0.013, wood, 0.008)
c = groups["Props"][1]
x, y = 6.12, 0.39
lathe(
    c,
    "羯鼓 · 朱漆鼓腔",
    (x, y, 0.12),
    [
        (0.30, 0),
        (0.32, 0.05),
        (0.255, 0.18),
        (0.225, 0.42),
        (0.29, 0.69),
        (0.355, 0.81),
        (0.35, 0.87),
    ],
    red,
    64,
)
lathe(
    c,
    "羯鼓 · 鼓皮",
    (x, y, 0.98),
    [(0.344, 0), (0.344, 0.014), (0.01, 0.019)],
    cream,
    64,
)
lathe(
    c,
    "羯鼓 · 鼓座",
    (x, y, 0),
    [(0.35, 0), (0.36, 0.03), (0.285, 0.08), (0.29, 0.13)],
    lac,
)
for j in range(24):
    a = math.tau * j / 24
    u, v = math.cos(a), math.sin(a)
    rod(
        c,
        "鼓边铜钉",
        (x + 0.337 * u, y + 0.337 * v, 0.965),
        (x + 0.355 * u, y + 0.355 * v, 0.965),
        0.009,
        brass,
    )
    if j % 2 == 0:
        line(
            c,
            "系革绳",
            [
                (x + 0.30 * u, y + 0.30 * v, 0.19),
                (x + 0.256 * u, y + 0.256 * v, 0.58),
                (x + 0.34 * u, y + 0.34 * v, 0.938),
            ],
            0.0048,
            bamboo,
        )
root, at = anchors["韩熙载·击鼓"]
for u, v in [(585, 99), (617, 140)]:
    mallet = rod(
        c,
        "击鼓槌",
        at(u, v, 0.035),
        (x + 0.09 + (u - 585) * 0.004, y - 0.02, 1.06),
        0.009,
        wood,
        0.014,
    )
    mallet.parent = root
    mallet.matrix_parent_inverse = root.matrix_world.inverted()
    mallet["figure"] = root.name
regrod("韩熙载·持槌送客", "散宴手槌", (308, 201), (387, 150), 0.008, wood)


def service(sec, x, y, z, n):
    c = groups["Props"][sec - 1]
    for i in range(n):
        px = x + (i - (n - 1) / 2) * 0.17
        lathe(
            c,
            "浅腹盘 · 足与内膛",
            (px, y, z),
            [
                (0.026, 0),
                (0.032, 0.009),
                (0.042, 0.018),
                (0.076, 0.032),
                (0.078, 0.039),
                (0.073, 0.042),
                (0.062, 0.033),
                (0.031, 0.018),
                (0.001, 0.018),
            ],
            cel,
            48,
        )
        lathe(
            c,
            "酒盏 · 内釉",
            (px, y + 0.12, z),
            [
                (0.018, 0),
                (0.019, 0.009),
                (0.027, 0.021),
                (0.034, 0.062),
                (0.033, 0.065),
                (0.03, 0.061),
                (0.020, 0.018),
                (0.001, 0.015),
            ],
            cream,
            36,
        )
        for j in range(3):
            ob = lathe(
                c,
                "果实",
                (px + (j - 1) * 0.021, y + (0.012 if j == 1 else 0), z + 0.021),
                [(0.009, 0), (0.016, 0.008), (0.012, 0.023), (0.002, 0.027)],
                red,
            )


service(1, 12.09, -1.07, 0.63, 5)
service(1, 10.49, -0.73, 0.47, 3)
service(5, -13.17, -0.59, 0.46, 3)
for x, y, z in [(11.63, -0.89, 0.63), (-12.87, -0.56, 0.46)]:
    c = groups["Props"][0 if x > 0 else 4]
    lathe(
        c,
        "执壶 · 圈足梨腹",
        (x, y, z),
        [
            (0.035, 0),
            (0.048, 0.015),
            (0.065, 0.045),
            (0.068, 0.10),
            (0.041, 0.15),
            (0.027, 0.166),
            (0.029, 0.201),
            (0.038, 0.207),
        ],
        cel,
        48,
    )
    line(
        c,
        "执壶提梁",
        [
            (x + 0.049, y, z + 0.055),
            (x + 0.108, y, z + 0.106),
            (x + 0.096, y, z + 0.167),
            (x + 0.029, y, z + 0.161),
        ],
        0.009,
        cel,
    )
    rod(
        c,
        "执壶流",
        (x - 0.047, y, z + 0.07),
        (x - 0.11, y, z + 0.155),
        0.018,
        cel,
        0.009,
    )
lathe(
    groups["Props"][2],
    "净手盆 · 内外壁",
    (-0.22, 0.32, 0.81),
    [
        (0.082, 0),
        (0.097, 0.016),
        (0.15, 0.069),
        (0.155, 0.079),
        (0.147, 0.081),
        (0.09, 0.022),
        (0.001, 0.018),
    ],
    brass,
    64,
)
# Pool of light is offset from the main route.
farewell_candles = set()
flame = material("烛芯发光", (0.99, 0.45, 0.10))
p = flame.node_tree.nodes.get("Principled BSDF")
p.inputs["Emission Color"].default_value = (1, 0.34, 0.065, 1)
p.inputs["Emission Strength"].default_value = 4.0
for i, (lo, hi) in enumerate(zones):
    x = lo + 0.37
    y = 1.83
    c = groups["Props"][i]
    before_candles = set(c.objects)
    lathe(
        c,
        "灯座",
        (x, y, 0),
        [
            (0.10, 0),
            (0.12, 0.025),
            (0.05, 0.063),
            (0.026, 0.18),
            (0.020, 0.73),
            (0.065, 0.76),
            (0.098, 0.79),
            (0.097, 0.81),
        ],
        brass,
    )
    lathe(c, "蜡烛", (x, y, 0.81), [(0.023, 0), (0.023, 0.14), (0.017, 0.146)], cream)
    lathe(
        c,
        "烛焰",
        (x, y, 0.954),
        [(0.006, 0), (0.013, 0.014), (0.007, 0.031), (0.001, 0.054)],
        flame,
    )
    light("烛光 " + events[i], "POINT", (x, y, 1.04), 14, (1, 0.45, 0.14), 0.09)

    if i == 4:
        farewell_candles = {ob.name for ob in set(c.objects) - before_candles}
