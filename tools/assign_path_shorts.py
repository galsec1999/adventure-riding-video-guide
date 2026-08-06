#!/usr/bin/env python3
"""Assign up to three exact-category Shorts to learning-path steps.

Document version: 2.0.0. There is no domain fallback: a step stays empty when
no strictly verified Short matches a full-video category in that step.
"""
import json
from collections import defaultdict
from pathlib import Path

root=Path(__file__).resolve().parents[1]
videos=json.loads((root/"data/videos.json").read_text(encoding="utf-8")); shorts=json.loads((root/"data/shorts.json").read_text(encoding="utf-8")); paths=json.loads((root/"data/learning-paths.json").read_text(encoding="utf-8"))
byid={v["id"]:v for v in videos}; pools=defaultdict(list)
for item in shorts: pools[item["primary_category"]].append(item)
used=defaultdict(int)
for path in paths:
  for step in path["steps"]:
    cats=[]
    for vid in step["primary_video_ids"]+step["alternative_video_ids"]:
      if vid in byid and byid[vid]["primary_category"] not in cats: cats.append(byid[vid]["primary_category"])
    choices=[]
    for cat in cats:
      pool=pools.get(cat,[])
      for _ in range(min(3,len(pool))):
        item=pool[used[cat]%len(pool)]; used[cat]+=1
        if item["id"] not in choices: choices.append(item["id"])
        if len(choices)==3: break
      if len(choices)==3: break
    step["short_video_ids"]=choices
(root/"data/learning-paths.json").write_text(json.dumps(paths,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(sum(len(p["steps"]) for p in paths),sum(len(s["short_video_ids"]) for p in paths for s in p["steps"]))
