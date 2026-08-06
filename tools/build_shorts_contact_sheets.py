#!/usr/bin/env python3
"""Download public thumbnails only and build numbered visual-review contact sheets."""
import argparse, io, json, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

p=argparse.ArgumentParser(); p.add_argument("--data",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--per-sheet",type=int,default=50); a=p.parse_args()
items=json.loads(a.data.read_text(encoding="utf-8")); a.output.mkdir(parents=True,exist_ok=True)
font=ImageFont.load_default(); cellw,cellh=320,230; cols=5; rows=(a.per_sheet+cols-1)//cols
for start in range(0,len(items),a.per_sheet):
    sheet=Image.new("RGB",(cols*cellw,rows*cellh),(24,28,32)); draw=ImageDraw.Draw(sheet)
    for offset,item in enumerate(items[start:start+a.per_sheet]):
        r,c=divmod(offset,cols); x,y=c*cellw,r*cellh
        try:
            req=urllib.request.Request(item["thumbnail_url"],headers={"User-Agent":"Mozilla/5.0"}); raw=urllib.request.urlopen(req,timeout=12).read()
            im=Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((cellw,180)); sheet.paste(im,(x+(cellw-im.width)//2,y))
        except Exception: draw.rectangle((x,y,x+cellw-1,y+180),fill=(70,30,30))
        text=f"{start+offset+1}. {item['channel_name'][:25]}\n{item['title_original'][:70]}"
        draw.multiline_text((x+5,y+183),text,fill="white",font=font,spacing=2)
    path=a.output/f"shorts-review-{start//a.per_sheet+1:02d}.jpg"; sheet.save(path,quality=88); print(path)
