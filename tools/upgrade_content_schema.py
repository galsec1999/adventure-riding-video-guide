#!/usr/bin/env python3
"""Conservative content-schema migration helper.

Document version: 1.0.0

The command is a dry run unless ``--write --output PATH`` is supplied.  It
never removes source fields and it does not infer facts that are absent from
the source document.  The default ``surface_scope`` is ``adventure`` because
the source guide is explicitly an Adventure Motorcycle guide; broadening a
card to road use requires later editorial review.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DOCUMENT_VERSION = "1.0.0"
DEFAULT_INPUT = Path("data/guide.json")

CARD_DEFAULTS: tuple[tuple[str, Any], ...] = (
    ("content_type", None),
    ("surface_scope", "adventure"),
    ("bike_classes", []),
    ("risk_level", None),
    ("content_status", "needs_review"),
    ("hero_video_id", None),
    ("official_source_refs", []),
    ("related_card_ids", []),
    ("duplicate_of", None),
)

VIDEO_DEFAULTS: tuple[tuple[str, Any], ...] = (
    ("channel_id", None),
    ("channel_title", None),
    ("published_at", None),
    ("duration_seconds", None),
    ("default_audio_language", None),
    ("caption_available", None),
    ("caption_languages", []),
    ("embeddable", None),
    ("availability_status", None),
    ("availability_checked_at", None),
    ("view_count", None),
    ("like_count", None),
    ("comment_count", None),
    ("metrics_fetched_at", None),
    ("thumbnail_url", None),
    ("authority_type", None),
    ("review_status", "unreviewed"),
    ("reviewed_at", None),
    ("reviewer", None),
    ("evidence_basis", None),
    ("transcript_reviewed", None),
    ("claims_checked", []),
    ("safety_flags", []),
    ("model_scope", []),
    ("year_scope", []),
    ("market_scope", []),
    ("quality_rubric", None),
)

# Only the identical title pair is marked as a duplicate.  The canonical card
# remains intact and the second card is retained with ``duplicate_of``.
EXACT_DUPLICATES: tuple[tuple[str, str], ...] = (("9.10", "17.6"),)

# These pairs overlap or one is a learning path for the other.  They are linked
# for editorial review, but are deliberately not labelled as duplicates.
RELATED_CARD_PAIRS: tuple[tuple[str, str], ...] = (
    ("9.11", "17.7"),
    ("11.3", "17.14"),
    ("15.9", "18.14"),
    ("15.16", "18.16"),
    ("6.14", "16.1"),
    ("6.15", "16.2"),
    ("6.17", "16.3"),
    ("6.7", "16.4"),
    ("15.3", "16.6"),
    ("15.13", "16.7"),
    ("15.10", "16.8"),
    ("15.12", "16.9"),
    ("15.18", "16.10"),
    ("4.9", "16.12"),
)

FULL_REVIEW_STATUSES = {
    "full_review",
    "full_watch",
    "fully_reviewed",
    "manual_reviewed",
}
TRANSCRIPT_REVIEW_STATUSES = {
    "transcript_review",
    "transcript_reviewed",
}
METADATA_REVIEW_STATUSES = {
    "metadata_screened",
    "pre_screened",
    "prescreened",
}


class MigrationError(ValueError):
    """Raised when an input cannot be migrated without guessing its shape."""


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise MigrationError(f"{path} must be a JSON array")
    return value


def _card_key(card: dict[str, Any]) -> str | None:
    value = card.get("id") or card.get("number")
    return str(value) if value not in (None, "") else None


def _iter_cards(document: dict[str, Any]) -> Iterable[dict[str, Any]]:
    chapters = _require_list(document.get("chapters", []), "chapters")
    for chapter_index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            raise MigrationError(f"chapters[{chapter_index}] must be an object")
        cards = _require_list(
            chapter.get("cards", []), f"chapters[{chapter_index}].cards"
        )
        for card_index, card in enumerate(cards):
            if not isinstance(card, dict):
                raise MigrationError(
                    f"chapters[{chapter_index}].cards[{card_index}] must be an object"
                )
            yield card


def _add_field(
    record: dict[str, Any],
    field: str,
    value: Any,
    counts: Counter[str],
) -> bool:
    if field in record:
        return False
    record[field] = copy.deepcopy(value)
    counts[field] += 1
    return True


def _normalise_review_status(video: dict[str, Any]) -> str:
    existing = video.get("review_status")
    if isinstance(existing, str) and existing.strip():
        return existing

    ai_review = video.get("ai_review")
    if not isinstance(ai_review, dict):
        return "unreviewed"

    raw_status = ai_review.get("status")
    status = str(raw_status).strip().lower() if raw_status is not None else ""
    if status in FULL_REVIEW_STATUSES:
        return "full_review"
    if status in TRANSCRIPT_REVIEW_STATUSES:
        return "transcript_reviewed"
    if status in METADATA_REVIEW_STATUSES:
        return "metadata_screened"
    return "unreviewed"


def _copy_explicit_review_evidence(
    video: dict[str, Any], counts: Counter[str]
) -> bool:
    ai_review = video.get("ai_review")
    if not isinstance(ai_review, dict):
        return False

    changed = False
    if "reviewed_at" not in video and ai_review.get("reviewed_on") not in (None, ""):
        video["reviewed_at"] = ai_review["reviewed_on"]
        counts["reviewed_at"] += 1
        changed = True
    if "evidence_basis" not in video and ai_review.get("basis") not in (None, ""):
        video["evidence_basis"] = ai_review["basis"]
        counts["evidence_basis"] += 1
        changed = True
    if "transcript_reviewed" not in video:
        status = _normalise_review_status(video)
        if status == "transcript_reviewed" or status == "full_review":
            video["transcript_reviewed"] = True
            counts["transcript_reviewed"] += 1
            changed = True
        elif ai_review.get("transcript_required") is True:
            video["transcript_reviewed"] = False
            counts["transcript_reviewed"] += 1
            changed = True
    return changed


def _append_unique(values: list[Any], item: str) -> bool:
    if item in values:
        return False
    values.append(item)
    return True


def migrate_document(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a migrated deep copy and a deterministic report.

    Existing values always win.  The function adds missing schema fields,
    copies only explicit legacy evidence, and records known duplicate/related
    pairs without deleting any card.
    """

    if not isinstance(document, dict):
        raise MigrationError("the JSON root must be an object")

    migrated = copy.deepcopy(document)
    cards = list(_iter_cards(migrated))
    videos = _require_list(migrated.get("videos", []), "videos")

    card_fields_added: Counter[str] = Counter()
    video_fields_added: Counter[str] = Counter()
    cards_changed: set[str] = set()
    videos_changed: set[str] = set()
    warnings: list[str] = []

    cards_by_number: dict[str, dict[str, Any]] = {}
    for index, card in enumerate(cards):
        number = card.get("number")
        if number not in (None, ""):
            number_key = str(number)
            if number_key in cards_by_number:
                warnings.append(f"duplicate card number: {number_key}")
            else:
                cards_by_number[number_key] = card

        key = _card_key(card) or f"card-index:{index}"
        changed = False
        for field, default in CARD_DEFAULTS:
            value = default
            if field == "official_source_refs":
                legacy = card.get("official_sources")
                value = list(legacy) if isinstance(legacy, list) else []
            changed |= _add_field(card, field, value, card_fields_added)
        if changed:
            cards_changed.add(key)

    for index, video in enumerate(videos):
        if not isinstance(video, dict):
            raise MigrationError(f"videos[{index}] must be an object")
        key = str(video.get("id") or f"video-index:{index}")
        changed = _copy_explicit_review_evidence(video, video_fields_added)
        for field, default in VIDEO_DEFAULTS:
            value = (
                _normalise_review_status(video)
                if field == "review_status"
                else default
            )
            changed |= _add_field(video, field, value, video_fields_added)
        if changed:
            videos_changed.add(key)

    duplicate_marks: list[dict[str, str]] = []
    related_links_added = 0

    def link_pair(left_number: str, right_number: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        nonlocal related_links_added
        left = cards_by_number.get(left_number)
        right = cards_by_number.get(right_number)
        if left is None or right is None:
            warnings.append(f"known card pair missing: {left_number} <-> {right_number}")
            return None
        left_key = _card_key(left)
        right_key = _card_key(right)
        if not left_key or not right_key:
            warnings.append(f"known card pair lacks id/number: {left_number} <-> {right_number}")
            return None
        left_related = left.get("related_card_ids")
        right_related = right.get("related_card_ids")
        if not isinstance(left_related, list) or not isinstance(right_related, list):
            warnings.append(f"related_card_ids is not an array: {left_number} <-> {right_number}")
            return None
        if _append_unique(left_related, right_key):
            related_links_added += 1
            cards_changed.add(left_key)
        if _append_unique(right_related, left_key):
            related_links_added += 1
            cards_changed.add(right_key)
        return left, right

    for canonical_number, duplicate_number in EXACT_DUPLICATES:
        pair = link_pair(canonical_number, duplicate_number)
        if pair is None:
            continue
        canonical, duplicate = pair
        canonical_key = _card_key(canonical)
        duplicate_key = _card_key(duplicate)
        current = duplicate.get("duplicate_of")
        if current in (None, ""):
            duplicate["duplicate_of"] = canonical_key
            cards_changed.add(duplicate_key or duplicate_number)
            duplicate_marks.append(
                {
                    "canonical": canonical_key or canonical_number,
                    "duplicate": duplicate_key or duplicate_number,
                }
            )
        elif current != canonical_key:
            warnings.append(
                f"preserved conflicting duplicate_of on {duplicate_key}: {current}"
            )

    for left_number, right_number in RELATED_CARD_PAIRS:
        link_pair(left_number, right_number)

    report = {
        "document_version": DOCUMENT_VERSION,
        "cards_seen": len(cards),
        "cards_changed": len(cards_changed),
        "videos_seen": len(videos),
        "videos_changed": len(videos_changed),
        "card_fields_added": dict(sorted(card_fields_added.items())),
        "video_fields_added": dict(sorted(video_fields_added.items())),
        "duplicate_marks": duplicate_marks,
        "related_links_added": related_links_added,
        "warnings": sorted(warnings),
        "would_change": migrated != document,
    }
    return migrated, report


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise MigrationError(f"{path} is not UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise MigrationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise MigrationError("the JSON root must be an object")
    return value, raw


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run a conservative schema migration for data/guide.json. "
            "No data file is written unless --write and --output are both supplied."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--write", action="store_true", help="write migrated JSON")
    parser.add_argument("--output", type=Path, help="required destination with --write")
    parser.add_argument(
        "--report",
        type=Path,
        help="optional JSON report path; stdout is always used as well",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when the input still requires migration",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.write and args.output is None:
        parser.error("--write requires --output")
    if args.output is not None and not args.write:
        parser.error("--output requires --write")

    try:
        source, raw = load_json(args.input)
        migrated, report = migrate_document(source)
    except (OSError, MigrationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    migrated_raw = _json_bytes(migrated)
    report["input"] = str(args.input)
    report["input_sha256"] = _sha256(raw)
    report["migrated_sha256"] = _sha256(migrated_raw)
    report["mode"] = "write" if args.write else "dry-run"

    if args.write:
        assert args.output is not None
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(migrated_raw)
        report["output"] = str(args.output)

    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_text, encoding="utf-8", newline="\n")
    print(report_text, end="")
    return 1 if args.check and report["would_change"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
