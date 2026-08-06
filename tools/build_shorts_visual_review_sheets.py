#!/usr/bin/env python3
"""Build compact two-frame contact sheets for Shorts visual review.

Document version: 1.0.0

The source frames are temporary QA artifacts captured from the public YouTube
player. The generated sheets are for human review only and are not published.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FRAME_SIZE = (200, 337)
BLOCK_SIZE = (430, 430)
SHEET_SIZE = (900, 1760)
ITEMS_PER_SHEET = 8


def load_font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "research" / "shorts-v3.3" / "source-audit.json")
    parser.add_argument("--frames", type=Path, default=ROOT / "research" / "shorts-v3.3" / ".visual-frames")
    parser.add_argument("--output", type=Path, default=ROOT / "research" / "shorts-v3.3" / ".visual-sheets")
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    item_map = {item["youtube_video_id"]: item for item in audit["items"]}
    available = []
    for video_id in audit["visual_review_queue_ids"]:
        frame_a = args.frames / f"{video_id}-a.png"
        frame_b = args.frames / f"{video_id}-b.png"
        if frame_a.exists() and frame_b.exists():
            available.append((item_map[video_id], frame_a, frame_b))

    args.output.mkdir(parents=True, exist_ok=True)
    title_font = load_font(18, bold=True)
    text_font = load_font(15)
    index = []
    for sheet_number, start in enumerate(range(0, len(available), ITEMS_PER_SHEET), 1):
        group = available[start : start + ITEMS_PER_SHEET]
        sheet = Image.new("RGB", SHEET_SIZE, "#101713")
        draw = ImageDraw.Draw(sheet)
        ids = []
        for position, (item, frame_a, frame_b) in enumerate(group):
            col = position % 2
            row = position // 2
            x = 15 + col * 440
            y = 15 + row * 435
            ids.append(item["youtube_video_id"])
            draw.rounded_rectangle((x, y, x + BLOCK_SIZE[0], y + BLOCK_SIZE[1]), radius=14, fill="#18251f", outline="#547060", width=2)
            with Image.open(frame_a) as image_a, Image.open(frame_b) as image_b:
                image_a = image_a.convert("RGB").resize(FRAME_SIZE)
                image_b = image_b.convert("RGB").resize(FRAME_SIZE)
                sheet.paste(image_a, (x + 10, y + 82))
                sheet.paste(image_b, (x + 220, y + 82))
            category = str(item.get("proposed_category") or "unknown")
            title = str(item.get("live_title") or "")
            channel = str(item.get("channel_name") or "")
            promo = ", ".join(item.get("description_marketing_markers") or []) or "none"
            draw.text((x + 10, y + 8), f"{item['youtube_video_id']}  |  {category}", font=title_font, fill="#f2f5ed")
            wrapped = textwrap.wrap(title, width=49)[:2]
            draw.text((x + 10, y + 32), "\n".join(wrapped), font=text_font, fill="#dce9df", spacing=2)
            draw.text((x + 10, y + 421), f"{channel[:32]} | captions {item.get('caption_chars') or 0} | promo {promo[:32]}", font=text_font, fill="#b8c8bd", anchor="ls")
        output_path = args.output / f"sheet-{sheet_number:02d}.jpg"
        sheet.save(output_path, quality=88, optimize=True)
        index.append({"sheet": output_path.name, "youtube_video_ids": ids})

    (args.output / "index.json").write_text(json.dumps({
        "document_version": "1.0.0",
        "product_version": "3.3.0",
        "available_items": len(available),
        "sheets": index,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(index)} sheets for {len(available)} Shorts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
