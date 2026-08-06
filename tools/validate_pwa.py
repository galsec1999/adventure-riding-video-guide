#!/usr/bin/env python3
"""Validate the publishable PWA without relying on a build step."""

from __future__ import annotations

import argparse
import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path

from jsonschema import Draft202012Validator


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for name in ("href", "src"):
            value = values.get(name)
            if value:
                self.paths.append(value)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(24)
    if signature[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", signature[16:24])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--schema", type=Path, default=Path("documentation/video.schema.json"))
    parser.add_argument("--expected-count", type=int, default=411)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    site = args.site.resolve()
    checks: list[dict[str, object]] = []

    def check(name: str, condition: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    required = [
        "index.html", "404.html", "offline.html", "manifest.webmanifest", "service-worker.js",
        "assets/css/styles.css", "assets/js/app.js", "assets/js/pwa.js", "assets/js/semantic-worker.js",
        "assets/vendor/transformers.min.js", "assets/vendor/ort-wasm-simd-threaded.mjs",
        "assets/vendor/ort-wasm-simd-threaded.wasm", "data/videos.json", "data/travel-guides.json",
        "data/semantic-index.json", "data/semantic-index.f32", "data/shorts.json", "data/site-config.json",
    ]
    for relative in required:
        check(f"required:{relative}", (site / relative).is_file())

    videos = json.loads((site / "data/videos.json").read_text(encoding="utf-8"))
    shorts = json.loads((site / "data/shorts.json").read_text(encoding="utf-8"))
    manifest = json.loads((site / "manifest.webmanifest").read_text(encoding="utf-8"))
    site_config = json.loads((site / "data/site-config.json").read_text(encoding="utf-8"))
    semantic_index = json.loads((site / "data/semantic-index.json").read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    check("videos:exact-count", len(videos) == args.expected_count, len(videos))
    check("videos:unique-id", len({item["id"] for item in videos}) == len(videos))
    check("videos:unique-youtube-id", len({item["youtube_video_id"] for item in videos}) == len(videos))
    check("videos:unique-url", len({item["youtube_url"] for item in videos}) == len(videos))
    check("shorts:non-empty", len(shorts) > 0, len(shorts))
    check("shorts:unique-id", len({item["id"] for item in shorts}) == len(shorts))
    check("catalogue:unique-youtube-id", len({item["youtube_video_id"] for item in [*videos, *shorts]}) == len(videos) + len(shorts))
    check("release:manifest-config", manifest.get("version") == site_config.get("release_version"), {
        "manifest": manifest.get("version"), "config": site_config.get("release_version"),
    })

    semantic_ids = semantic_index.get("ids", [])
    dimensions = semantic_index.get("dimensions")
    check("semantic:count", semantic_index.get("count") == len(videos), semantic_index.get("count"))
    check("semantic:ids", semantic_ids == [item["id"] for item in videos])
    check("semantic:dimensions", isinstance(dimensions, int) and dimensions > 0, dimensions)
    semantic_binary = site / "data/semantic-index.f32"
    if semantic_binary.is_file() and isinstance(dimensions, int) and dimensions > 0:
        expected_bytes = len(videos) * dimensions * 4
        check("semantic:binary-size", semantic_binary.stat().st_size == expected_bytes, {
            "actual": semantic_binary.stat().st_size, "expected": expected_bytes,
        })

    standalone_name = str(site_config.get("standalone_filename", ""))
    standalone = site / "downloads" / standalone_name
    check("standalone:configured", bool(standalone_name) and standalone.is_file(), standalone_name)
    if standalone.is_file():
        standalone_text = standalone.read_text(encoding="utf-8")
        check("standalone:release", f'data-release="{manifest.get("version", "")}"' in standalone_text)
        embedded_videos = re.search(
            r'<script id="embedded-data-videos" type="application/json">([\s\S]*?)</script>',
            standalone_text,
        )
        embedded_count = None
        if embedded_videos:
            embedded_count = len(json.loads(embedded_videos.group(1).replace("<\\/script", "</script")))
        check("standalone:count", embedded_count == len(videos), embedded_count)
        embedded_shorts = re.search(
            r'<script id="embedded-data-shorts" type="application/json">([\s\S]*?)</script>',
            standalone_text,
        )
        embedded_shorts_count = None
        if embedded_shorts:
            embedded_shorts_count = len(json.loads(embedded_shorts.group(1).replace("<\\/script", "</script")))
        check("standalone:shorts-count", embedded_shorts_count == len(shorts), embedded_shorts_count)

    for index, video in enumerate(videos):
        errors = sorted(validator.iter_errors(video), key=lambda error: list(error.path))
        check(f"schema:{index}:{video.get('id', 'unknown')}", not errors, [error.message for error in errors[:5]])
        expected_suffix = f"watch?v={video['youtube_video_id']}"
        check(f"youtube-url:{index}", expected_suffix in video["youtube_url"], video["youtube_url"])

    required_manifest = {
        "id": "./", "scope": "./", "display": "standalone", "lang": "he", "dir": "rtl",
    }
    for key, expected in required_manifest.items():
        check(f"manifest:{key}", manifest.get(key) == expected, manifest.get(key))
    check("manifest:start-url-relative", str(manifest.get("start_url", "")).startswith("./"), manifest.get("start_url"))
    check("manifest:display-override", manifest.get("display_override") == ["standalone", "minimal-ui"])
    check("manifest:prefer-related-applications", manifest.get("prefer_related_applications") is False)

    for entry in [*manifest.get("icons", []), *manifest.get("screenshots", [])]:
        source = str(entry.get("src", ""))
        relative = source.removeprefix("./")
        target = site / relative
        check(f"manifest-file:{relative}", target.is_file())
        if target.is_file() and target.suffix.lower() == ".png" and entry.get("sizes"):
            declared = tuple(int(value) for value in str(entry["sizes"]).split("x"))
            check(f"png-size:{relative}", png_size(target) == declared, {"actual": png_size(target), "declared": declared})

    for shortcut in manifest.get("shortcuts", []):
        check(f"shortcut-relative:{shortcut.get('name')}", str(shortcut.get("url", "")).startswith("./#"), shortcut.get("url"))

    html = (site / "index.html").read_text(encoding="utf-8")
    asset_parser = AssetParser()
    asset_parser.feed(html)
    for value in asset_parser.paths:
        if value.startswith(("#", "mailto:", "http://", "https://", "data:")):
            continue
        path_only = value.split("#", 1)[0].split("?", 1)[0].removeprefix("./")
        if path_only:
            check(f"html-asset:{path_only}", (site / path_only).is_file())

    text_files = [site / "index.html", site / "manifest.webmanifest", *site.glob("assets/js/*.js")]
    absolute_pattern = re.compile(r"(?:href|src|fetch\(|register\()\s*[=:]?\s*[\"']/((?:assets|data|manifest|service-worker)[^\"']*)")
    for path in text_files:
        content = path.read_text(encoding="utf-8")
        check(f"subpath-safe:{path.relative_to(site).as_posix()}", absolute_pattern.search(content) is None)

    worker = (site / "service-worker.js").read_text(encoding="utf-8")
    expected_cache = f"adventure-guide-v{manifest.get('version', '')}"
    for token in [expected_cache, "SKIP_WAITING", "clients.claim", "./data/videos.json", "./offline.html"]:
        check(f"worker:{token}", token in worker)
    for forbidden in ["youtube.com", "youtube-nocookie.com", "googlevideo.com"]:
        check(f"worker:no-{forbidden}", forbidden not in worker)

    failed = [item for item in checks if not item["passed"]]
    report = {
        "document_version": "1.1.0",
        "product_version": manifest.get("version"),
        "status": "PASS" if not failed else "FAIL",
        "site": str(site),
        "expected_video_count": args.expected_count,
        "video_count": len(videos),
        "shorts_count": len(shorts),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "checks": checks,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "video_count", "checks_passed", "checks_failed")}, ensure_ascii=False))
    if failed:
        for item in failed[:20]:
            print(f"FAIL {item['name']}: {item['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
