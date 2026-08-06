#!/usr/bin/env python3
"""Retired unsafe title/thumbnail-only Shorts builder.

Document version: 2.0.0. Product 3.2.0 requires title, source description and
individual visual review. Use audit_shorts_content.py and
apply_shorts_content_audit.py instead.
"""

from __future__ import annotations

import argparse, json, re
from collections import Counter
from datetime import date
from pathlib import Path

from tools.build_shorts_library import CATEGORY_HE, NON_EDUCATIONAL_RE, PROMO_RE, classify, round_robin_candidates


TODAY = date.today().isoformat()


def record(item, topic):
    vid=item["youtube_video_id"]; channel=item["channel_name"]; title=item["title_original"]
    cat=topic["category"]; he=CATEGORY_HE[cat]; en=cat.replace("_"," ")
    risk="medium" if topic["domain"] in {"road","offroad_adventure"} else "low"
    return {
      "id":f"yts-{vid}","youtube_video_id":vid,"youtube_url":f"https://www.youtube.com/shorts/{vid}","thumbnail_url":f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
      "title_original":title,"title_he":f"קצר: {title}","title_en":title,"channel_name":channel,"channel_url":f"https://www.youtube.com/channel/{item['channel_id']}",
      "published_date":None,"duration_seconds":None,"language":"en","subtitle_languages":[],"domain":topic["domain"],"primary_category":cat,"secondary_categories":[],"subtopics":[topic["sub"]],
      "content_type":"drill" if cat=="drills" else "explainer","tags":topic["tags"],"skill_level":"beginner" if risk=="low" else "advanced_beginner","risk_level":risk,
      "motorcycle_types":["general_motorcycle"],"motorcycle_weight_classes":["general"],"terrain_types":[],"road_conditions":[],
      "summary_he":f"קטע קצר מערוץ {channel} שסווג בזהירות בנושא {he} לאחר בדיקת רשומת Shorts ותמונת התצוגה. יש לפתוח את המקור לקבלת ההדגמה וההקשר שהיוצר מספק.",
      "summary_en":f"A short clip from {channel}, conservatively classified under {en} after reviewing the Shorts listing and thumbnail. Open the source for the creator's demonstration and context.",
      "learning_points_he":[f"לזהות נקודה קצרה בנושא {he}","לבחון את ההדגמה בהקשר המקורי","להמשיך להסבר מלא לפני תרגול"],
      "learning_points_en":[f"Identify one quick point about {en}","Review the demonstration in its original context","Continue to a full explanation before practice"],
      "fit_for_he":"מתאים כרענון מהיר בלבד; אינו תחליף לשיעור מלא או להדרכה מעשית.","fit_for_en":"Suitable only as a quick refresher; it does not replace a full lesson or practical instruction.",
      "why_watch_he":f"נקודת כניסה מהירה לנושא {he} לפני לימוד מעמיק.","why_watch_en":f"A quick entry point to {en} before deeper study.",
      "exercises_he":[],"exercises_en":[],"equipment_he":["ציוד מיגון מתאים"],"equipment_en":["Appropriate protective riding gear"],
      "safety_warnings_he":["קצר עשוי להשמיט תנאים וסיכונים; אין לתרגל על סמך הקטע לבדו."],"safety_warnings_en":["A Short may omit conditions and risks; do not practise from the clip alone."],
      "common_mistakes_he":["להסיק כלל מלא מקטע קצר"],"common_mistakes_en":["Treating a brief clip as a complete rule"],"chapters":[],"quality_score":2,
      "quality_reason_he":"הקישור זוהה בלשונית Shorts הציבורית של הערוץ, ותמונת התצוגה נבדקה חזותית. ללא תיאור או תמלול זמין, עומק האימות מוגבל ומסומן בשקיפות.",
      "quality_reason_en":"The link was identified on the channel's public Shorts tab and its thumbnail was visually reviewed. With no available description or transcript, verification depth is limited and disclosed.",
      "source_type":"professional_instructor","contains_marketing":False,"related_video_ids":[],
      "verification":{"link_status":"active_public","metadata_verified":True,"content_evidence_types":["youtube_search_metadata","visual_review"],"classification_confidence":"low",
        "notes_he":f"נבדק ב־{TODAY}; לא הורדו וידאו, אודיו או תמלול.","notes_en":f"Checked on {TODAY}; no video, audio or transcript was downloaded."},
      "last_checked":TODAY,"media_format":"short"
    }


def main():
    raise SystemExit(
        "Retired in product 3.2.0: title/thumbnail-only classification is forbidden. "
        "Use tools/audit_shorts_content.py followed by tools/apply_shorts_content_audit.py."
    )
    p=argparse.ArgumentParser(); p.add_argument("--candidates",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--target",type=int,default=1000); p.add_argument("--exclusions",type=Path); a=p.parse_args()
    src=json.loads(a.candidates.read_text(encoding="utf-8")); selected=[]
    for item in round_robin_candidates(src["candidates"]):
        title=item.get("title_original") or ""
        if PROMO_RE.search(title) or NON_EDUCATIONAL_RE.search(title): continue
        topic=classify(title)
        if not topic: continue
        selected.append(record(item,topic))
        if len(selected)>=a.target: break
    if a.exclusions:
        excluded=set(json.loads(a.exclusions.read_text(encoding="utf-8"))["excluded_one_based_indexes"])
        selected=[item for index,item in enumerate(selected,1) if index not in excluded]
    a.output.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"count":len(selected),"channels":Counter(x["channel_name"] for x in selected),"categories":Counter(x["primary_category"] for x in selected)},ensure_ascii=False,default=dict))
    return 0 if len(selected)==a.target else 2

if __name__=="__main__": raise SystemExit(main())
