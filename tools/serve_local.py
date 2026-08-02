#!/usr/bin/env python3
"""Serve the project over HTTP for local development and review.

The server uses only Python's standard library, binds to localhost by default,
serves the repository root regardless of the caller's working directory, and
disables directory listings and browser caching.
"""

from __future__ import annotations

import argparse
import functools
import mimetypes
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ProjectRequestHandler(SimpleHTTPRequestHandler):
    """Static-file handler with development-friendly and safer defaults."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def list_directory(self, path: str):  # type: ignore[override]
        self.send_error(404, "Directory listing is disabled")
        return None


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the Adventure Riding Video Guide locally."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Address to bind (default: 127.0.0.1; use 0.0.0.0 only on a trusted network).",
    )
    parser.add_argument(
        "--port",
        default=8000,
        type=int,
        help="TCP port (default: 8000; use 0 to select an available port).",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open the site in the default browser after the server starts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 <= args.port <= 65535:
        print("ERROR: --port must be between 0 and 65535.", file=sys.stderr)
        return 2

    index_path = PROJECT_ROOT / "index.html"
    if not index_path.is_file():
        print(f"ERROR: site entry point not found: {index_path}", file=sys.stderr)
        return 2

    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("application/json", ".json")
    mimetypes.add_type("image/svg+xml", ".svg")

    handler = functools.partial(ProjectRequestHandler, directory=str(PROJECT_ROOT))
    try:
        server = LocalThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        print(f"ERROR: could not start the local server: {exc}", file=sys.stderr)
        return 1

    actual_port = server.server_address[1]
    browser_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    url = f"http://{browser_host}:{actual_port}/"
    print(f"Serving {PROJECT_ROOT}")
    print(f"Open {url}")
    print("Press Ctrl+C to stop.")

    if args.open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
