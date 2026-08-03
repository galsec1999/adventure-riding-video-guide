#!/usr/bin/env python3
"""Legacy Wave 1 entry point; delegates all validation to validate_data.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from validate_data import main as validate_data_main
    from validate_data import positive_int
except ModuleNotFoundError:  # Supports `python -m tools.validate_wave1`.
    from tools.validate_data import main as validate_data_main
    from tools.validate_data import positive_int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Legacy Wave 1 validator. An explicit expected count is required; "
            "use tools/validate_data.py directly for release validation."
        )
    )
    parser.add_argument(
        "--expected-count",
        type=positive_int,
        required=True,
        help="Historical Wave 1 count (normally 60); no default is assumed",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--report", type=Path, help="Also write the JSON report to this path")
    args = parser.parse_args(argv)

    print(
        "WARNING: validate_wave1.py is a legacy phase-specific wrapper; "
        "use validate_data.py for release validation.",
        file=sys.stderr,
    )
    forwarded = ["--expected-count", str(args.expected_count)]
    if args.json:
        forwarded.append("--json")
    if args.report:
        forwarded.extend(("--report", str(args.report)))
    return validate_data_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
