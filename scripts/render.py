"""Render the study views from the open .blend using Cycles."""
import argparse
from pathlib import Path
import sys
import bpy
p=argparse.ArgumentParser()
p.add_argument("--out",type=Path,default=Path(__file__).resolve().parents[1]/"renders")
p.add_argument("--percent",type=int,default=100)
p.add_argument("--samples",type=int,default=24)
p.add_argument("--views",default="1,2,3,4,5,6,7")
a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
a.out.mkdir(exist_ok=True,parents=True)
s=bpy.context.scene
names=["overview","screen-before","screen-after","gap","listening","winds","table-detail"]
for num in [int(v) for v in a.views.split(",")]:
    s.frame_set(1+(num-1)*24);s.cycles.samples=a.samples
    s.render.resolution_x=1820 if num==1 else 1320;s.render.resolution_y=650 if num==1 else 820
    s.render.resolution_percentage=a.percent;s.render.filepath=str((a.out/(names[num-1]+".png")).resolve())
    bpy.ops.render.render(write_still=True)
