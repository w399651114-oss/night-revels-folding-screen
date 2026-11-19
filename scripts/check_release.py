"""Fast offline release checks for CI, requiring only standard-library Python."""
import ast
import hashlib
import json
from pathlib import Path
import struct

root=Path(__file__).resolve().parents[1]
for p in (root/"scripts").glob("*.py"):ast.parse(p.read_text(),filename=p.name)
for line in (root/"SHA256SUMS").read_text().splitlines():
    digest,name=line.split("  ",1)
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
actors=json.loads((root/"assets/figures.json").read_text())
report=json.loads((root/"docs/measurements.json").read_text())
assert len(actors)==report["characters"]==43
assert [sum(a["section"]==s for a in actors) for s in range(1,6)]==report["characters_by_section"]
assert sum(report["collections"].values())==report["objects"]
for a in actors:
    assert len(a["outline"])>20 and all(0<=x<=4633 and 0<=y<=400 for x,y in a["outline"])
for name in ["overview","screen-before","screen-after","gap","listening","winds","table-detail"]:
    raw=(root/"renders"/(name+".png")).read_bytes()
    assert raw[:8]==b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II",raw[16:24])==((1820,650) if name=="overview" else (1320,820))
assert report["figure_furniture_surface_crossings"]==0 and len(report["depth_bands"])==5
assert (root/"docs/提示词原文.txt").stat().st_size>2000
print("Verified publication assets, all seven renders, scene inventory and Python sources.")
