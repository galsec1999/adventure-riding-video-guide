#!/usr/bin/env python3
"""Build the documented single-file edition from the canonical v3 sources."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = (
    ("videos", "videos.json"),
    ("categories", "categories.json"),
    ("learning-paths", "learning-paths.json"),
    ("synonyms", "synonyms.json"),
    ("site-config", "site-config.json"),
    ("travel-guides", "travel-guides.json"),
)
MODULES = ("storage.js", "search.js", "pagination.js", "i18n.js", "app.js")


def script_safe(value: str) -> str:
    return re.sub(r"</script", r"<\\/script", value, flags=re.IGNORECASE)


def bundle_modules() -> str:
    pieces: list[str] = []
    for filename in MODULES:
        source = (ROOT / "assets" / "js" / filename).read_text(encoding="utf-8")
        if filename == "app.js":
            source = re.sub(r"\A(?:import[\s\S]*?from\s+[\"'][^\"']+[\"'];\s*)+", "", source)
        source = re.sub(r"(?m)^export\s+", "", source)
        pieces.append(f"\n// ---- {filename} ----\n{source.strip()}\n")
    return script_safe("".join(pieces))


def build() -> Path:
    config = json.loads((ROOT / "data" / "site-config.json").read_text(encoding="utf-8"))
    filename = config["standalone_filename"]
    version = config["release_version"]
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "assets" / "css" / "styles.css").read_text(encoding="utf-8")

    html = re.sub(r"<link[^>]+rel=[\"']manifest[\"'][^>]*>\s*", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<link[^>]+rel=[\"'](?:apple-touch-icon|icon)[\"'][^>]*>\s*", "", html, flags=re.IGNORECASE)
    html = re.sub(
        r"<link[^>]+href=[\"']\./assets/css/styles\.css(?:\?[^\"']*)?[\"'][^>]*>",
        f"<style>\n{css}\n</style>",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(r"<script[^>]+src=[\"']\./assets/js/(?:app|pwa)\.js(?:\?[^\"']*)?[\"'][^>]*></script>\s*", "", html, flags=re.IGNORECASE)
    html = re.sub(r'data-standalone="false"', 'data-standalone="true"', html, count=1)
    html = re.sub(r'data-release="[^"]+"', f'data-release="{version}"', html, count=1)

    embedded: list[str] = []
    for element_id, filename_part in DATA_FILES:
        raw = (ROOT / "data" / filename_part).read_text(encoding="utf-8").strip()
        embedded.append(
            f'<script id="embedded-data-{element_id}" type="application/json">{script_safe(raw)}</script>'
        )
    payload = "\n".join(embedded) + f"\n<script type=\"module\">\n{bundle_modules()}\n</script>\n"
    html = html.replace("</body>", f"{payload}</body>", 1)
    html = re.sub(r"(?:<!DOCTYPE html>\s*)+", "<!DOCTYPE html>\n", html, count=1, flags=re.IGNORECASE)

    output = ROOT / "downloads" / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")

    videos = json.loads((ROOT / "data" / "videos.json").read_text(encoding="utf-8"))
    rendered = output.read_text(encoding="utf-8")
    if not re.match(r"\A<!DOCTYPE html>\s*<html\b", rendered, flags=re.IGNORECASE):
        raise SystemExit("Standalone must begin with one doctype followed by the HTML element")
    if 'data-standalone="true"' not in rendered or f'data-release="{version}"' not in rendered:
        raise SystemExit("Standalone release markers are missing")
    embedded_videos = re.search(
        r'<script id="embedded-data-videos" type="application/json">([\s\S]*?)</script>', rendered
    )
    if not embedded_videos or len(json.loads(embedded_videos.group(1).replace("<\\/script", "</script"))) != len(videos):
        raise SystemExit("Standalone embedded video count does not match the catalogue")
    if "semantic-worker.js" in rendered and "data-standalone=\"true\"" not in rendered:
        raise SystemExit("Standalone local-AI guard is missing")
    print(f"Built {output.relative_to(ROOT)} with {len(videos)} videos for version {version}.")
    return output


if __name__ == "__main__":
    build()
