#!/usr/bin/env python3
"""Apply the product 3.3.0 version and content-count bump.

Document version: 1.0.0
Product version: 3.3.0
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD = "3.2.0"
NEW = "3.3.0"
OLD_REV = "3.2.0-20260806a"
NEW_REV = "3.3.0-20260806a"
TOTAL = 563
SHORTS = 152


def replace(path: Path, pairs: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    replace(ROOT / "index.html", [
        (OLD_REV, NEW_REV),
        (f"v{OLD}-Standalone.html", f"v{NEW}-Standalone.html"),
        (OLD, NEW),
    ])
    replace(ROOT / "assets/js/app.js", [(OLD_REV, NEW_REV)])
    replace(ROOT / "service-worker.js", [
        ("PWA release 3.2.0 — strict Shorts content audit and local semantic runtime.",
         "PWA release 3.3.0 — source-verified Shorts recovery and local semantic runtime."),
        (OLD_REV, NEW_REV),
        (OLD, NEW),
    ])
    for path in (ROOT / "schema/video.schema.json", ROOT / "documentation/video.schema.json"):
        replace(path, [(OLD, NEW)])

    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    manifest["version"] = NEW
    manifest["description"] = f"{TOTAL} הדרכות רכיבה פעילות ומסווגות, ובהן {SHORTS} קצרים שעברו אימות מקור ובדיקה חזותית, בעברית ובאנגלית."
    json_write(ROOT / "manifest.webmanifest", manifest)

    config_path = ROOT / "data/site-config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config.update({
        "document_title": "תצורת אתר מדריך הווידאו הקהילתי לרכיבת אדוונצ'ר",
        "document_version": "3.3.0",
        "meta_title_he": f"מדריך הווידאו הקהילתי לרכיבת אדוונצ'ר — גרסה {NEW}",
        "meta_description_he": f"{TOTAL} הדרכות רכיבה פעילות ומסווגות, ובהן {SHORTS} קצרים שעברו אימות מקור ובדיקה חזותית, מסלולי לימוד וחיפוש חכם בעברית ובאנגלית.",
        "release_version": NEW,
        "standalone_filename": f"Adventure-Riding-Video-Guide-v{NEW}-Standalone.html",
        "meta_title_en": f"Community Adventure Riding Video Guide — Version {NEW}",
        "meta_description_en": f"{TOTAL} active, curated riding tutorials, including {SHORTS} Shorts that passed source and visual review, with learning paths and smart search in Hebrew and English.",
    })
    json_write(config_path, config)

    for filename in ("package.json", "package-lock.json"):
        path = ROOT / filename
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("version") == OLD:
            value["version"] = NEW
        if isinstance(value.get("packages"), dict) and isinstance(value["packages"].get(""), dict):
            if value["packages"][""].get("version") == OLD:
                value["packages"][""]["version"] = NEW
        json_write(path, value)

    print(json.dumps({"product_version": NEW, "total_items": TOTAL, "shorts": SHORTS}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
