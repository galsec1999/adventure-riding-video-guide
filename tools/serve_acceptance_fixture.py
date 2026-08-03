#!/usr/bin/env python3
"""Serve an ephemeral 130/300-record acceptance fixture without changing production."""

from __future__ import annotations

import argparse
import functools
import json
import mimetypes
import shutil
import sys
import tempfile
from pathlib import Path

try:
    from fixture_factory import build_video_fixture, load_json
    from serve_local import LocalThreadingHTTPServer, ProjectRequestHandler
    from validate_data import positive_int
except ModuleNotFoundError:  # Supports `python -m tools.serve_acceptance_fixture`.
    from tools.fixture_factory import build_video_fixture, load_json
    from tools.serve_local import LocalThreadingHTTPServer, ProjectRequestHandler
    from tools.validate_data import positive_int


ROOT = Path(__file__).resolve().parents[1]
CONFIG_MODES = (
    "production",
    "custom-logo",
    "empty-logo",
    "missing-logo",
    "empty-optionals",
    "unsafe-logo",
)
FIXTURE_LOGO = """<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96" role="img" aria-label="לוגו בדיקת תצורה">
  <rect width="96" height="96" rx="20" fill="#173f35"/>
  <path d="M16 68 36 31l12 21 10-15 22 31Z" fill="#f3b640"/>
</svg>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=positive_int, required=True, help="Ephemeral video count, normally 130 or 300")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=0, help="TCP port (default: 0, choose an available port)")
    parser.add_argument(
        "--config-mode",
        choices=CONFIG_MODES,
        default="production",
        help="Optional temporary site-config customization scenario",
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    return args


def prepare_site(root: Path, count: int, config_mode: str) -> None:
    shutil.copy2(ROOT / "index.html", root / "index.html")
    shutil.copytree(ROOT / "assets", root / "assets")
    shutil.copytree(ROOT / "data", root / "data")

    source_videos = load_json(ROOT / "data" / "videos.json")
    fixture = build_video_fixture(source_videos, count)
    (root / "data" / "videos.json").write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if config_mode == "production":
        return
    config_path = root / "data" / "site-config.json"
    config = load_json(config_path)
    config.update(
        {
            "site_name_he": "מדריך בדיקת תצורה",
            "author_name": "מחבר בדיקת קבלה",
            "community_name": "קהילת בדיקות מקומית",
            "contact": "",
        }
    )
    if config_mode == "custom-logo":
        logo_path = root / "assets" / "acceptance-fixture-logo.svg"
        logo_path.write_text(FIXTURE_LOGO, encoding="utf-8")
        config["logo_path"] = "assets/acceptance-fixture-logo.svg"
    elif config_mode == "missing-logo":
        config["logo_path"] = "assets/acceptance-fixture-missing.svg"
    elif config_mode == "unsafe-logo":
        config["logo_path"] = "javascript:alert(1)"
    elif config_mode == "empty-optionals":
        config.update(
            {
                "author_name": "",
                "community_name": "",
                "contact": "",
                "logo_path": "",
            }
        )
    else:
        config["logo_path"] = ""
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="adv-guide-acceptance-") as temp_dir:
        site_root = Path(temp_dir)
        try:
            prepare_site(site_root, args.count, args.config_mode)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: could not prepare fixture: {exc}", file=sys.stderr)
            return 2
        mimetypes.add_type("application/javascript", ".js")
        mimetypes.add_type("application/json", ".json")
        mimetypes.add_type("image/svg+xml", ".svg")
        handler = functools.partial(ProjectRequestHandler, directory=str(site_root))
        try:
            server = LocalThreadingHTTPServer((args.host, args.port), handler)
        except OSError as exc:
            print(f"ERROR: could not start fixture server: {exc}", file=sys.stderr)
            return 1
        actual_port = server.server_address[1]
        browser_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
        print(
            f"Fixture: count={args.count}; config={args.config_mode}; persistent_files=0",
            flush=True,
        )
        print(f"Open http://{browser_host}:{actual_port}/", flush=True)
        print("Press Ctrl+C to stop and delete the temporary fixture.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping acceptance fixture server.")
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
