"""Optional outline regeneration. Inputs are in 4633 x 400 study coordinates."""
from pathlib import Path
import json
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
offsets=[3580,2750,2115,1000,0]
cv2.setNumThreads(1)
scroll=cv2.imread(str(ROOT/'assets/scroll.jpg'))
sx,sy=scroll.shape[1]/4633,scroll.shape[0]/400
records=[]
for row in (ROOT/'assets/tracings.txt').read_text().splitlines():
    if not row or row.startswith('#'):continue
    section,name,pose,outline=row.split('|')
    sec=int(section);xy=np.array([tuple(map(int,p.split(','))) for p in outline.split()],dtype=float)
    xy[:,0]+=offsets[sec-1];xy*=np.array([sx,sy]);xy=np.round(xy).astype(np.int32)
    x,y,w,h=cv2.boundingRect(xy);x=max(0,x-20);y=max(0,y-20)
    tile=scroll[y:y+h+40,x:x+w+40].copy();mask=np.zeros(tile.shape[:2],np.uint8)
    cv2.fillPoly(mask,[xy-[x,y]],255)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(19,19))
    gc=np.zeros_like(mask);gc[cv2.dilate(mask,kernel)>0]=2;gc[mask>0]=3;gc[cv2.erode(mask,kernel)>0]=1
    cv2.setRNGSeed(963)
    cv2.grabCut(tile,gc,None,np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_MASK)
    contours,_=cv2.findContours((gc%2).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    pts=cv2.approxPolyDP(max(contours,key=cv2.contourArea),1.65,True)[:,0,:]+[x,y]
    pts=np.round(pts/[sx,sy],3)
    records.append(dict(section=sec,name=name,pose=list(map(float,pose.split())),outline=pts.tolist()))
(ROOT/'assets/figures.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':'))+'\n')
