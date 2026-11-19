"""Publish source annotations and contact sheets. Requires optional Pillow 13.0.0."""

import argparse
import json
import statistics
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--out", type=Path, default=ROOT / "docs/plates")
p.add_argument(
    "--frames", type=Path, help="Parent of main, control, off frame directories"
)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
src = Image.open(ROOT / "assets/scroll.jpg").convert("RGB")
figures = json.loads((ROOT / "assets/figures.json").read_text())
ids = json.loads((ROOT / "assets/figure-ids.json").read_text())
windows = [(3580, 4633), (2750, 3590), (2115, 2795), (1000, 1970), (0, 975)]
# Each pair of strokes is project-authored digit geometry, avoiding a font dependency.
segments = [
    (0, 0, 4, 0),
    (4, 0, 4, 4),
    (4, 4, 4, 8),
    (4, 8, 0, 8),
    (0, 8, 0, 4),
    (0, 4, 0, 0),
    (0, 4, 4, 4),
]
digits = [
    "012345",
    "12",
    "01643",
    "01623",
    "5612",
    "05623",
    "056432",
    "012",
    "0123456",
    "015623",
]


def tag(draw, x, y, n):
    draw.rounded_rectangle(
        (x - 15, y - 11, x + 15, y + 11),
        radius=4,
        fill="#24382f",
        outline="#f8e9bd",
        width=1,
    )
    for i, k in enumerate(f"{n:02}"):
        for segment in digits[int(k)]:
            x1, y1, x2, y2 = segments[int(segment)]
            ox = x - 10 + 12 * i
            draw.line(
                (ox + x1 * 2, y - 8 + y1 * 2, ox + x2 * 2, y - 8 + y2 * 2),
                fill="#fff7dd",
                width=2,
            )


def crop(box, size):
    x0, y0, x1, y1 = box
    rect = (
        x0 * src.width / 4633,
        y0 * src.height / 400,
        x1 * src.width / 4633,
        y1 * src.height / 400,
    )
    return src.resize(size, Image.Resampling.LANCZOS, box=rect)


def save(img, name):
    img.save(a.out / name, quality=90, subsampling=0, optimize=True)


for section, (left, right) in enumerate(windows, 1):
    scale = 1.35
    canvas = crop(
        (left, 0, right, 400), (round((right - left) * scale), round(400 * scale))
    )
    draw = ImageDraw.Draw(canvas, "RGBA")
    tags = []
    for rec in (f for f in figures if f["section"] == section):
        poly = [((x - left) * scale, y * scale) for x, y in rec["outline"]]
        draw.line(poly + [poly[0]], fill=(255, 229, 162, 200), width=2)
        top = min(y for x, y in poly)
        anchor_x = statistics.median(x for x, y in poly if y < top + 12)
        x = min(max(16, anchor_x), canvas.width - 16)
        y = max(13, top - 16)
        while any(abs(x - xx) < 32 and abs(y - yy) < 24 for xx, yy in tags):
            y += 24
        tags.append((x, y))
        draw.line((x, y, anchor_x, top + 2), fill=(255, 243, 195, 255), width=2)
        tag(draw, x, y, int(ids[rec["name"]].split("F")[1]))
    save(canvas, f"source-{section}.jpg")

details = [
    (
        "D01",
        (3594, 14, 3779, 126),
        "屏心 · 山水绢本",
        "画中屏心取样。双面构造、扇数与铰接属 H。",
    ),
    (
        "D02",
        (3625, 163, 3764, 270),
        "曲项琵琶 · 原卷面板",
        "乐器外线与持物方向可见。弦距、厚度与背面属 H。",
    ),
    (
        "D03",
        (3260, 115, 3420, 346),
        "羯鼓 · 朱漆鼓腔",
        "朱鼓外形与击鼓关系可见。系绳数、剖面与木座属 H。",
    ),
    (
        "D04",
        (3080, 92, 3139, 150),
        "檀木拍板 1",
        "观舞段持板者双手之间的局部。板数与厚度属 H。",
    ),
    (
        "D05",
        (2214, 207, 2321, 282),
        "净手盆 · 内外壁",
        "案榻前手、盆与递接姿态。盆的内腔和支承属 H。",
    ),
    (
        "D06",
        (1227, 72, 1548, 160),
        "横笛 · 管身 / 筚篥类纵管 · 管身",
        "清吹手口及所持管身局部。器种细分、孔位与演奏指法待考。",
    ),
    (
        "D07",
        (275, 130, 413, 229),
        "散宴手槌",
        "送客者手边细部。持物身份依据释读，三维长度属 H。",
    ),
    (
        "D08",
        (833, 8, 1120, 390),
        "四 · 留白出口 · 独扇山水 / GapCorridor",
        "散宴与清吹之间的画面接合，可查屏、人物与绢底。两条实验阈线没有对应的底本坐标。",
    ),
]
for key, box, _, _ in details:
    w, h = box[2] - box[0], box[3] - box[1]
    factor = min(540 / w, 360 / h)
    save(crop(box, (round(w * factor), round(h * factor))), key + ".jpg")
lines = [
    "# 底本定位索引",
    "",
    "坐标以仓库原图左上为原点，统一换算到 4633 × 400。人物轮廓收在 figures.json，ID 与姓名的固定映射收在 figure-ids.json。在 Blender 的 Outliner 搜索姓名，选中人物操作柄或彩墨浅浮雕即可读到相同的 source_id。段内图上的两位数对应 F 后的编号。轮廓记录当前数字描摹边界，贴近重叠处时应放大原卷核对。",
    "",
]
for i, (lo, hi) in enumerate(windows, 1):
    lines += [
        f"## 第 {i} 段 · " + ["听乐", "观舞", "暂歇", "清吹", "散宴"][i - 1],
        "",
        f"![分段底本与轮廓编号](plates/source-{i}.jpg)",
        "",
        f"取景 X 为 {lo}–{hi}。相邻人物可进入取景边缘。",
        "",
        "| 稳定编号 | 人物操作柄 | 底本轮廓框 x₀, y₀ → x₁, y₁ |",
        "|---|---|---|",
    ]
    for f in (rec for rec in figures if rec["section"] == i):
        x, y = zip(*f["outline"])
        lines.append(
            f"| {ids[f['name']]} | {f['name']} | {min(x):.1f}, {min(y):.1f} → {max(x):.1f}, {max(y):.1f} |"
        )
    lines.append("")
lines += [
    "## 屏、器物和留白的局部",
    "",
    "| 局部原图 | 归一化取景框 | 对应对象或集合 | 证据与推定 |",
    "|---|---|---|---|",
]
for key, box, obj, note in details:
    lines.append(
        f"| [{key} 原图](plates/{key}.jpg) | {', '.join(map(str, box))} | {obj} | {note} |"
    )
lines += [
    "",
    "笙与笙匣单列为工程补型（H），未分配底本局部编号。人物身份沿用馆方释读及工程命名。纵深、补片背面和五段真实距离均由建模设定。",
]
(a.out.parent / "底本定位.md").write_text("\n".join(lines) + "\n")

if a.frames:

    def sheet(name, rows):
        width, height = 528, 328
        gap = 4
        out = Image.new(
            "RGB",
            ((width + gap) * len(rows[0]) - gap, (height + gap) * len(rows) - gap),
            "#ebdcc1",
        )
        for j, row in enumerate(rows):
            for i, (case, frame) in enumerate(row):
                with Image.open(a.frames / case / f"f{frame:03}.png") as im:
                    assert im.size == (width, height)
                    out.paste(im, (i * (width + gap), j * (height + gap)))
        save(out, name + ".jpg")

    sheet("screen-test", [[("main", 25), ("off", 25)]])
    sheet("screen-walk", [[("main", i) for i in (217, 239, 267, 313)]])
    sheet(
        "gap-walk",
        [[(case, i) for i in (337, 365, 391, 429)] for case in ("main", "control")],
    )
