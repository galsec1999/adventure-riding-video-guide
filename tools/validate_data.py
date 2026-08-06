#!/usr/bin/env python3
"""Validate every project data structure without modifying project files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import urlsplit

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # Reported as a validation failure with an actionable message.
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = {
    "videos": ROOT / "data" / "videos.json",
    "shorts": ROOT / "data" / "shorts.json",
    "taxonomy": ROOT / "data" / "categories.json",
    "learning_paths": ROOT / "data" / "learning-paths.json",
    "travel_guides": ROOT / "data" / "travel-guides.json",
    "synonyms": ROOT / "data" / "synonyms.json",
    "site_config": ROOT / "data" / "site-config.json",
    "video_schema": ROOT / "schema" / "video.schema.json",
}

HEBREW_RE = re.compile(r"[\u0590-\u05ff]")
LATIN_RE = re.compile(r"[A-Za-z]")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLACEHOLDER_RE = re.compile(
    r"(?:lorem\s+ipsum|placeholder|dummy\s+data|sample\s+data|"
    r"example\.(?:com|org|net)|<untitled\s+chapter\s+\d+>|"
    r"\b(?:todo|tbd)\b|נתוני\s+דמה|טקסט\s+לדוגמה)",
    re.IGNORECASE,
)


@dataclass
class ValidationAudit:
    checks_passed: int = 0
    checks_failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    count_expectation: dict[str, Any] = field(
        default_factory=lambda: {
            "mode": "none",
            "value": None,
            "actual": None,
            "satisfied": False,
        }
    )

    def check(
        self,
        condition: bool,
        code: str,
        message: str,
        *,
        path: str | None = None,
        details: Any = None,
    ) -> bool:
        if condition:
            self.checks_passed += 1
            return True
        self.checks_failed += 1
        issue: dict[str, Any] = {"code": code, "message": message}
        if path is not None:
            issue["path"] = path
        if details is not None:
            issue["details"] = details
        self.errors.append(issue)
        return False

    def warn(self, code: str, message: str, *, path: str | None = None) -> None:
        warning: dict[str, Any] = {"code": code, "message": message}
        if path is not None:
            warning["path"] = path
        self.warnings.append(warning)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "pass" if self.checks_failed == 0 else "fail",
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "count_expectation": self.count_expectation,
            "stats": self.stats,
        }


def load_json(path: Path, audit: ValidationAudit, label: str) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        audit.check(False, "file.missing", f"Required file is missing: {path}", path=label)
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        audit.check(False, "file.invalid_json", f"Cannot read valid UTF-8 JSON: {exc}", path=label)
        return None
    audit.check(True, "file.valid_json", f"Loaded {label}", path=label)
    return value


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def has_hebrew(value: Any) -> bool:
    return isinstance(value, str) and HEBREW_RE.search(value) is not None


def has_latin(value: Any) -> bool:
    return isinstance(value, str) and LATIN_RE.search(value) is not None


def valid_https_url(value: Any) -> bool:
    if not is_nonempty_string(value) or any(character.isspace() for character in value):
        return False
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port  # Validate an explicitly supplied port, if any.
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and hostname
        and parsed.username is None
        and parsed.password is None
    )


def valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def require_keys(
    audit: ValidationAudit,
    value: Any,
    keys: Iterable[str],
    path: str,
) -> bool:
    if not audit.check(isinstance(value, dict), "structure.object", "Expected an object", path=path):
        return False
    missing = sorted(set(keys) - set(value))
    return audit.check(
        not missing,
        "structure.required_keys",
        f"Missing required keys: {', '.join(missing)}",
        path=path,
        details=missing or None,
    )


def duplicate_values(values: Iterable[Any]) -> list[Any]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates, key=str)


def validate_count_options(
    expected_count: int | None,
    minimum_count: int | None,
) -> None:
    """Reject contradictory or nonsensical count policies for API callers."""

    if expected_count is not None and minimum_count is not None:
        raise ValueError("expected_count and minimum_count cannot be used together")
    for name, value in (
        ("expected_count", expected_count),
        ("minimum_count", minimum_count),
    ):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value <= 0):
            raise ValueError(f"{name} must be a positive integer")


def describe_count_expectation(
    *,
    expected_count: int | None,
    minimum_count: int | None,
    actual: int | None,
) -> dict[str, Any]:
    if expected_count is not None:
        mode = "expected"
        value = expected_count
        satisfied = actual == expected_count
    elif minimum_count is not None:
        mode = "minimum"
        value = minimum_count
        satisfied = actual is not None and actual >= minimum_count
    else:
        mode = "none"
        value = None
        satisfied = actual is not None and actual > 0
    return {
        "mode": mode,
        "value": value,
        "actual": actual,
        "satisfied": satisfied,
    }


def walk_strings(value: Any, path: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, f"{path}.{key}")


def validate_taxonomy(audit: ValidationAudit, taxonomy: Any) -> dict[str, set[str]]:
    sections = (
        "domains",
        "categories",
        "subcategories",
        "content_types",
        "terrain_types",
        "road_conditions",
        "skill_levels",
        "risk_levels",
        "motorcycle_types",
        "motorcycle_weight_classes",
        "source_types",
        "languages",
        "controlled_tags",
    )
    allowed = {section: set() for section in sections}
    if not require_keys(audit, taxonomy, ("version", "updated", *sections), "data/categories.json"):
        return allowed
    audit.check(is_nonempty_string(taxonomy["version"]), "taxonomy.version", "Version must be non-empty", path="data/categories.json.version")
    audit.check(valid_iso_date(taxonomy["updated"]), "taxonomy.updated", "Updated must be an ISO date", path="data/categories.json.updated")
    for section in sections:
        items = taxonomy.get(section)
        section_path = f"data/categories.json.{section}"
        if not audit.check(isinstance(items, list) and bool(items), "taxonomy.section", "Taxonomy section must be a non-empty array", path=section_path):
            continue
        ids: list[str] = []
        for index, item in enumerate(items):
            item_path = f"{section_path}[{index}]"
            if not require_keys(audit, item, ("id", "name_he", "name_en", "description_he", "description_en"), item_path):
                continue
            identifier = item.get("id")
            audit.check(is_nonempty_string(identifier) and SLUG_RE.fullmatch(identifier) is not None, "taxonomy.id", "Taxonomy ID must be a lowercase slug", path=f"{item_path}.id")
            for field_name in ("name_he", "name_en", "description_he", "description_en"):
                audit.check(is_nonempty_string(item.get(field_name)), "taxonomy.text", f"{field_name} must be non-empty", path=f"{item_path}.{field_name}")
            audit.check(has_hebrew(item.get("description_he")), "taxonomy.hebrew", "Hebrew description must contain Hebrew text", path=f"{item_path}.description_he")
            if isinstance(identifier, str):
                ids.append(identifier)
        duplicates = duplicate_values(ids)
        audit.check(not duplicates, "taxonomy.duplicate_id", f"Duplicate IDs: {duplicates}", path=section_path, details=duplicates or None)
        allowed[section] = set(ids)
    return allowed


def validate_domain_category_map(
    audit: ValidationAudit,
    taxonomy: Any,
    videos: Any,
    allowed: dict[str, set[str]],
) -> None:
    mapping = taxonomy.get("domain_category_map") if isinstance(taxonomy, dict) else None
    if not audit.check(
        isinstance(mapping, dict),
        "taxonomy.domain_category_map",
        "domain_category_map must be an object",
        path="data/categories.json.domain_category_map",
    ):
        return

    domain_ids = allowed["domains"]
    category_ids = allowed["categories"]
    unknown_domains = sorted(set(mapping) - domain_ids)
    missing_domains = sorted(domain_ids - set(mapping))
    audit.check(
        not unknown_domains,
        "taxonomy.domain_category_map_domain",
        f"Unknown domains in domain_category_map: {unknown_domains}",
        path="data/categories.json.domain_category_map",
        details=unknown_domains or None,
    )
    audit.check(
        not missing_domains,
        "taxonomy.domain_category_map_domain",
        f"Domains missing from domain_category_map: {missing_domains}",
        path="data/categories.json.domain_category_map",
        details=missing_domains or None,
    )

    normalized: dict[str, set[str]] = {}
    for domain, categories in mapping.items():
        path = f"data/categories.json.domain_category_map.{domain}"
        array_ok = isinstance(categories, list) and bool(categories)
        audit.check(array_ok, "taxonomy.domain_category_map_array", "Mapped categories must be a non-empty array", path=path)
        if not array_ok:
            continue
        values_ok = all(is_nonempty_string(category) for category in categories)
        audit.check(
            values_ok,
            "taxonomy.domain_category_map_value",
            "Mapped category IDs must be non-empty strings",
            path=path,
        )
        valid_values = [category for category in categories if is_nonempty_string(category)]
        duplicates = duplicate_values(valid_values)
        unknown_categories = sorted(set(valid_values) - category_ids)
        audit.check(
            not duplicates,
            "taxonomy.domain_category_map_duplicate",
            f"Duplicate mapped categories: {duplicates}",
            path=path,
            details=duplicates or None,
        )
        audit.check(
            not unknown_categories,
            "taxonomy.domain_category_map_category",
            f"Unknown mapped categories: {unknown_categories}",
            path=path,
            details=unknown_categories or None,
        )
        normalized[domain] = set(valid_values) & category_ids

    mismatches: list[dict[str, str]] = []
    if isinstance(videos, list):
        for video in videos:
            if not isinstance(video, dict):
                continue
            domain = video.get("domain")
            category = video.get("primary_category")
            if domain in normalized and category not in normalized[domain]:
                mismatches.append(
                    {
                        "id": str(video.get("id", "<unknown>")),
                        "domain": str(domain),
                        "primary_category": str(category),
                    }
                )
    audit.check(
        not mismatches,
        "video.domain_category",
        f"Videos with a primary category outside their domain mapping: {len(mismatches)}",
        path="data/videos.json",
        details=mismatches or None,
    )
    audit.stats["domain_category_pairs"] = sum(len(categories) for categories in normalized.values())


def validate_video_schema(audit: ValidationAudit, schema: Any, videos: Any) -> None:
    if Draft202012Validator is None or FormatChecker is None:
        audit.check(False, "dependency.jsonschema", "Install jsonschema to run Draft 2020-12 validation")
        return
    if not isinstance(schema, dict):
        audit.check(False, "schema.object", "Video schema must be an object", path="schema/video.schema.json")
        return
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema raises SchemaError subclasses.
        audit.check(False, "schema.invalid", f"Invalid Draft 2020-12 schema: {exc}", path="schema/video.schema.json")
        return
    audit.check(True, "schema.valid", "Video schema is valid Draft 2020-12", path="schema/video.schema.json")
    if not isinstance(videos, list):
        return
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for index, video in enumerate(videos):
        errors = sorted(validator.iter_errors(video), key=lambda item: list(item.absolute_path))
        details = [
            {
                "path": ".".join(map(str, error.absolute_path)),
                "message": error.message,
            }
            for error in errors
        ]
        audit.check(
            not errors,
            "video.schema",
            f"Video record has {len(errors)} schema error(s)",
            path=f"data/videos.json[{index}]",
            details=details or None,
        )


def validate_videos(
    audit: ValidationAudit,
    videos: Any,
    allowed: dict[str, set[str]],
    *,
    expected_count: int | None = None,
    minimum_count: int | None = None,
) -> set[str]:
    if not audit.check(isinstance(videos, list), "videos.array", "videos.json must contain an array", path="data/videos.json"):
        return set()
    audit.check(bool(videos), "videos.nonempty", "videos.json must contain at least one video", path="data/videos.json")
    if expected_count is not None:
        audit.check(
            len(videos) == expected_count,
            "videos.expected_count",
            f"Expected exactly {expected_count} videos; found {len(videos)}",
            path="data/videos.json",
        )
    elif minimum_count is not None:
        audit.check(
            len(videos) >= minimum_count,
            "videos.minimum_count",
            f"Expected at least {minimum_count} videos; found {len(videos)}",
            path="data/videos.json",
        )
    mappings = {
        "domain": allowed["domains"],
        "primary_category": allowed["categories"],
        "content_type": allowed["content_types"],
        "skill_level": allowed["skill_levels"],
        "risk_level": allowed["risk_levels"],
        "source_type": allowed["source_types"],
        "language": allowed["languages"],
    }
    array_mappings = {
        "secondary_categories": allowed["categories"],
        "subtopics": allowed["subcategories"],
        "tags": allowed["controlled_tags"],
        "motorcycle_types": allowed["motorcycle_types"],
        "motorcycle_weight_classes": allowed["motorcycle_weight_classes"],
        "terrain_types": allowed["terrain_types"],
        "road_conditions": allowed["road_conditions"],
        "subtitle_languages": allowed["languages"],
    }
    internal_ids = [video.get("id") for video in videos if isinstance(video, dict)]
    youtube_ids = [video.get("youtube_video_id") for video in videos if isinstance(video, dict)]
    urls = [video.get("youtube_url") for video in videos if isinstance(video, dict)]
    for field_name, values in (("id", internal_ids), ("youtube_video_id", youtube_ids), ("youtube_url", urls)):
        duplicates = duplicate_values(values)
        audit.check(not duplicates, "videos.duplicate", f"Duplicate {field_name} values: {duplicates}", path="data/videos.json", details=duplicates or None)
    internal_set = {value for value in internal_ids if isinstance(value, str)}
    for index, video in enumerate(videos):
        path = f"data/videos.json[{index}]"
        if not isinstance(video, dict):
            audit.check(False, "video.object", "Video record must be an object", path=path)
            continue
        youtube_id = video.get("youtube_video_id")
        valid_youtube_id = isinstance(youtube_id, str) and YOUTUBE_ID_RE.fullmatch(youtube_id) is not None
        audit.check(valid_youtube_id, "video.youtube_id", "YouTube ID must be exactly 11 valid characters", path=f"{path}.youtube_video_id")
        if valid_youtube_id:
            short_format = video.get("media_format") == "short"
            expected_id = f"yts-{youtube_id}" if short_format else f"yt-{youtube_id}"
            audit.check(video.get("id") == expected_id, "video.internal_id", "Internal ID must match its media format and YouTube ID", path=f"{path}.id")
            expected_url = f"https://www.youtube.com/shorts/{youtube_id}" if short_format else f"https://www.youtube.com/watch?v={youtube_id}"
            audit.check(video.get("youtube_url") == expected_url, "video.youtube_url", "YouTube URL does not match the Video ID", path=f"{path}.youtube_url")
            thumbnail_url = video.get("thumbnail_url")
            thumbnail = urlsplit(thumbnail_url) if isinstance(thumbnail_url, str) else None
            thumbnail_ok = bool(
                thumbnail
                and thumbnail.scheme == "https"
                and (thumbnail.hostname or "").lower().endswith("ytimg.com")
                and f"/vi/{youtube_id}/" in thumbnail.path
            )
            audit.check(thumbnail_ok, "video.thumbnail_url", "Thumbnail URL must be an HTTPS ytimg URL for the same Video ID", path=f"{path}.thumbnail_url")
        channel_url = video.get("channel_url")
        parsed_channel = urlsplit(channel_url) if isinstance(channel_url, str) else None
        audit.check(
            bool(parsed_channel and parsed_channel.scheme == "https" and (parsed_channel.hostname or "").lower().endswith("youtube.com")),
            "video.channel_url",
            "Channel URL must be an HTTPS youtube.com URL",
            path=f"{path}.channel_url",
        )
        for field_name, allowed_values in mappings.items():
            audit.check(video.get(field_name) in allowed_values, "video.reference", f"Unknown {field_name}: {video.get(field_name)!r}", path=f"{path}.{field_name}")
        for field_name, allowed_values in array_mappings.items():
            values = video.get(field_name)
            unknown = sorted(set(values or []) - allowed_values) if isinstance(values, list) else ["<not-an-array>"]
            audit.check(not unknown, "video.reference_array", f"Unknown {field_name} values: {unknown}", path=f"{path}.{field_name}", details=unknown or None)
        for field_name in ("title_he", "summary_he", "fit_for_he", "why_watch_he", "quality_reason_he"):
            audit.check(has_hebrew(video.get(field_name)), "video.hebrew", f"{field_name} must contain Hebrew text", path=f"{path}.{field_name}")
        for field_name in ("learning_points_he", "exercises_he", "equipment_he", "safety_warnings_he", "common_mistakes_he"):
            values = video.get(field_name)
            invalid = [item for item in values or [] if not has_hebrew(item)] if isinstance(values, list) else [values]
            audit.check(not invalid, "video.hebrew_array", f"Every {field_name} item must contain Hebrew text", path=f"{path}.{field_name}", details=invalid or None)
        verification = video.get("verification")
        if isinstance(verification, dict):
            audit.check(verification.get("link_status") == "active_public", "video.link_status", "Recorded link status must be active_public", path=f"{path}.verification.link_status")
            audit.check(verification.get("metadata_verified") is True, "video.metadata_verified", "Metadata must be recorded as verified", path=f"{path}.verification.metadata_verified")
            evidence = verification.get("content_evidence_types")
            audit.check(isinstance(evidence, list) and bool(evidence), "video.evidence", "At least one content evidence type is required", path=f"{path}.verification.content_evidence_types")
            audit.check(has_hebrew(verification.get("notes_he")), "video.verification_hebrew", "Verification notes must contain Hebrew text", path=f"{path}.verification.notes_he")
        related = video.get("related_video_ids")
        if isinstance(related, list):
            unknown_related = sorted(set(related) - internal_set)
            audit.check(not unknown_related, "video.related_reference", f"Unknown related video IDs: {unknown_related}", path=f"{path}.related_video_ids", details=unknown_related or None)
            audit.check(video.get("id") not in related, "video.related_self", "A video must not relate to itself", path=f"{path}.related_video_ids")
        chapters = video.get("chapters")
        if isinstance(chapters, list):
            previous_start = -1
            for chapter_index, chapter in enumerate(chapters):
                chapter_path = f"{path}.chapters[{chapter_index}]"
                if not isinstance(chapter, dict):
                    continue
                start = chapter.get("start_seconds")
                end = chapter.get("end_seconds")
                if isinstance(start, int):
                    audit.check(start >= previous_start, "video.chapter_order", "Chapters must be ordered by start time", path=chapter_path)
                    previous_start = start
                if isinstance(start, int) and isinstance(end, int):
                    audit.check(end >= start, "video.chapter_range", "Chapter end must not precede its start", path=chapter_path)
                    duration = video.get("duration_seconds")
                    if isinstance(duration, int):
                        audit.check(end <= duration + 2, "video.chapter_duration", "Chapter exceeds video duration by more than two seconds", path=chapter_path)
    return internal_set


def validate_learning_paths(
    audit: ValidationAudit,
    paths: Any,
    internal_ids: set[str],
    skill_levels: set[str],
    risk_levels: set[str],
) -> None:
    if not audit.check(isinstance(paths, list), "paths.array", "learning-paths.json must contain an array", path="data/learning-paths.json"):
        return
    audit.check(len(paths) >= 8, "paths.count", f"Expected at least eight learning paths; found {len(paths)}", path="data/learning-paths.json")
    path_ids = [item.get("id") for item in paths if isinstance(item, dict)]
    duplicates = duplicate_values(path_ids)
    audit.check(not duplicates, "paths.duplicate_id", f"Duplicate learning-path IDs: {duplicates}", path="data/learning-paths.json", details=duplicates or None)
    total_steps = 0
    total_references = 0
    for path_index, learning_path in enumerate(paths):
        path_name = f"data/learning-paths.json[{path_index}]"
        if not require_keys(audit, learning_path, ("id", "name_he", "description_he", "skill_level", "steps"), path_name):
            continue
        audit.check(is_nonempty_string(learning_path["id"]) and SLUG_RE.fullmatch(learning_path["id"]) is not None, "paths.id", "Learning-path ID must be a lowercase slug", path=f"{path_name}.id")
        audit.check(has_hebrew(learning_path["name_he"]), "paths.hebrew", "Learning-path name must contain Hebrew", path=f"{path_name}.name_he")
        audit.check(has_hebrew(learning_path["description_he"]), "paths.hebrew", "Learning-path description must contain Hebrew", path=f"{path_name}.description_he")
        audit.check(learning_path["skill_level"] in skill_levels, "paths.skill_level", "Unknown learning-path skill level", path=f"{path_name}.skill_level")
        steps = learning_path["steps"]
        if not audit.check(isinstance(steps, list) and bool(steps), "paths.steps", "Learning path must contain steps", path=f"{path_name}.steps"):
            continue
        audit.check(8 <= len(steps) <= 12, "paths.step_count", f"Learning path must contain 8-12 steps; found {len(steps)}", path=f"{path_name}.steps")
        total_steps += len(steps)
        orders = [step.get("order") for step in steps if isinstance(step, dict)]
        audit.check(orders == list(range(1, len(steps) + 1)), "paths.step_order", "Step order must be consecutive and match array order", path=f"{path_name}.steps")
        for step_index, step in enumerate(steps):
            step_path = f"{path_name}.steps[{step_index}]"
            if not require_keys(audit, step, ("order", "goal_he", "explanation_he", "primary_video_ids", "alternative_video_ids", "short_video_ids", "equipment_he", "risk_level", "warning_he"), step_path):
                continue
            audit.check(has_hebrew(step["goal_he"]), "paths.hebrew", "Step goal must contain Hebrew", path=f"{step_path}.goal_he")
            audit.check(has_hebrew(step["explanation_he"]), "paths.hebrew", "Step explanation must contain Hebrew", path=f"{step_path}.explanation_he")
            audit.check(isinstance(step["equipment_he"], list) and bool(step["equipment_he"]) and all(has_hebrew(item) for item in step["equipment_he"]), "paths.equipment", "Step equipment must be a non-empty Hebrew array", path=f"{step_path}.equipment_he")
            audit.check(step["risk_level"] in risk_levels, "paths.risk_level", "Unknown step risk level", path=f"{step_path}.risk_level")
            audit.check(has_hebrew(step["warning_he"]), "paths.warning", "Step warning must contain Hebrew", path=f"{step_path}.warning_he")
            primary = step["primary_video_ids"]
            alternatives = step["alternative_video_ids"]
            shorts = step["short_video_ids"]
            arrays_ok = isinstance(primary, list) and isinstance(alternatives, list) and isinstance(shorts, list)
            audit.check(arrays_ok, "paths.video_arrays", "Primary and alternative IDs must be arrays", path=step_path)
            if not arrays_ok:
                continue
            total_references += len(primary) + len(alternatives) + len(shorts)
            audit.check(bool(primary), "paths.primary", "Every step must include at least one primary video", path=f"{step_path}.primary_video_ids")
            audit.check(bool(alternatives), "paths.alternative", "Every step must include at least one alternative video", path=f"{step_path}.alternative_video_ids")
            audit.check(len(shorts) >= 2, "paths.shorts", "Every step must include at least two Shorts", path=f"{step_path}.short_video_ids")
            all_refs = primary + alternatives
            audit.check(2 <= len(all_refs) <= 5, "paths.video_count", f"Every step must reference 2-5 videos; found {len(all_refs)}", path=step_path)
            unknown = sorted(set(all_refs) - internal_ids)
            audit.check(not unknown, "paths.reference", f"Unknown video IDs: {unknown}", path=step_path, details=unknown or None)
            duplicate_refs = duplicate_values(all_refs)
            audit.check(not duplicate_refs, "paths.duplicate_reference", f"Duplicate/overlapping step video IDs: {duplicate_refs}", path=step_path, details=duplicate_refs or None)
            unknown_shorts = sorted(set(shorts) - internal_ids)
            audit.check(not unknown_shorts, "paths.short_reference", f"Unknown Short IDs: {unknown_shorts}", path=step_path, details=unknown_shorts or None)
    audit.stats["learning_paths"] = len(paths)
    audit.stats["learning_path_steps"] = total_steps
    audit.stats["learning_path_video_references"] = total_references


def validate_bilingual_text_fields(
    audit: ValidationAudit,
    value: dict[str, Any],
    stems: Iterable[str],
    path: str,
) -> None:
    for stem in stems:
        hebrew_key = f"{stem}_he"
        english_key = f"{stem}_en"
        hebrew_value = value.get(hebrew_key)
        english_value = value.get(english_key)
        audit.check(
            is_nonempty_string(hebrew_value) and has_hebrew(hebrew_value),
            "travel.bilingual_hebrew",
            f"{hebrew_key} must be non-empty Hebrew text",
            path=f"{path}.{hebrew_key}",
        )
        audit.check(
            is_nonempty_string(english_value) and has_latin(english_value),
            "travel.bilingual_english",
            f"{english_key} must be non-empty English text",
            path=f"{path}.{english_key}",
        )


def validate_bilingual_list_fields(
    audit: ValidationAudit,
    value: dict[str, Any],
    stems: Iterable[str],
    path: str,
    *,
    expected_items: int | None = None,
    every_hebrew_item: bool = False,
) -> None:
    for stem in stems:
        hebrew_key = f"{stem}_he"
        english_key = f"{stem}_en"
        hebrew_values = value.get(hebrew_key)
        english_values = value.get(english_key)
        hebrew_ok = (
            isinstance(hebrew_values, list)
            and bool(hebrew_values)
            and all(is_nonempty_string(item) for item in hebrew_values)
        )
        english_ok = (
            isinstance(english_values, list)
            and bool(english_values)
            and all(is_nonempty_string(item) for item in english_values)
        )
        audit.check(
            hebrew_ok,
            "travel.bilingual_array",
            f"{hebrew_key} must be a non-empty array of strings",
            path=f"{path}.{hebrew_key}",
        )
        audit.check(
            english_ok,
            "travel.bilingual_array",
            f"{english_key} must be a non-empty array of strings",
            path=f"{path}.{english_key}",
        )
        if not (hebrew_ok and english_ok):
            continue
        assert isinstance(hebrew_values, list)
        assert isinstance(english_values, list)
        audit.check(
            len(hebrew_values) == len(english_values),
            "travel.bilingual_array_length",
            f"{hebrew_key} and {english_key} must contain the same number of entries",
            path=path,
        )
        if expected_items is not None:
            audit.check(
                len(hebrew_values) == expected_items and len(english_values) == expected_items,
                "travel.bilingual_array_count",
                f"{hebrew_key} and {english_key} must each contain exactly {expected_items} entries",
                path=path,
            )
        hebrew_content_ok = (
            all(has_hebrew(item) for item in hebrew_values)
            if every_hebrew_item
            else has_hebrew(" ".join(hebrew_values))
        )
        audit.check(
            hebrew_content_ok,
            "travel.bilingual_hebrew",
            f"{hebrew_key} must contain Hebrew content",
            path=f"{path}.{hebrew_key}",
        )
        audit.check(
            all(has_latin(item) for item in english_values),
            "travel.bilingual_english",
            f"Every {english_key} entry must contain English text",
            path=f"{path}.{english_key}",
        )


def validate_travel_video_ids(
    audit: ValidationAudit,
    value: Any,
    internal_ids: set[str],
    path: str,
) -> int:
    array_ok = isinstance(value, list) and bool(value) and all(is_nonempty_string(item) for item in value)
    audit.check(
        array_ok,
        "travel.video_ids",
        "video_ids must be a non-empty array of video IDs",
        path=path,
    )
    if not array_ok:
        return 0
    valid_values = [item for item in value if isinstance(item, str)]
    duplicates = duplicate_values(valid_values)
    unknown = sorted(set(valid_values) - internal_ids)
    audit.check(
        not duplicates,
        "travel.duplicate_video_id",
        f"Duplicate video IDs: {duplicates}",
        path=path,
        details=duplicates or None,
    )
    audit.check(
        not unknown,
        "travel.video_reference",
        f"Unknown video IDs: {unknown}",
        path=path,
        details=unknown or None,
    )
    return len(valid_values)


def validate_travel_guides(
    audit: ValidationAudit,
    travel: Any,
    internal_ids: set[str],
    learning_path_ids: set[str],
) -> None:
    root_path = "data/travel-guides.json"
    required_top_level = (
        "version",
        "updated",
        "trip_types",
        "checklists",
        "navigation_apps",
        "mindfulness_note_he",
        "mindfulness_note_en",
        "knowledge_guides",
    )
    if not require_keys(audit, travel, required_top_level, root_path):
        return
    assert isinstance(travel, dict)
    audit.check(
        is_nonempty_string(travel["version"]) and SEMVER_RE.fullmatch(travel["version"]) is not None,
        "travel.version",
        "Travel-guide version must be a semantic version",
        path=f"{root_path}.version",
    )
    audit.check(
        valid_iso_date(travel["updated"]),
        "travel.updated",
        "Travel-guide updated value must be an ISO date",
        path=f"{root_path}.updated",
    )
    validate_bilingual_text_fields(audit, travel, ("mindfulness_note",), root_path)

    trip_types = travel["trip_types"]
    trip_array_ok = isinstance(trip_types, list)
    audit.check(trip_array_ok, "travel.trip_types_array", "trip_types must be an array", path=f"{root_path}.trip_types")
    if trip_array_ok:
        assert isinstance(trip_types, list)
        audit.check(
            len(trip_types) == 3,
            "travel.trip_types_count",
            f"Expected exactly three trip types; found {len(trip_types)}",
            path=f"{root_path}.trip_types",
        )
        trip_ids = [item.get("id") for item in trip_types if isinstance(item, dict)]
        audit.check(
            set(trip_ids) == {"day", "multi_day", "abroad"} and len(trip_ids) == 3,
            "travel.trip_type_ids",
            "Trip types must be day, multi_day and abroad",
            path=f"{root_path}.trip_types",
            details=trip_ids,
        )
        for index, trip_type in enumerate(trip_types):
            path = f"{root_path}.trip_types[{index}]"
            if not require_keys(
                audit,
                trip_type,
                ("id", "name_he", "name_en", "description_he", "description_en", "recommended_path_id"),
                path,
            ):
                continue
            assert isinstance(trip_type, dict)
            audit.check(
                is_nonempty_string(trip_type["id"]) and SLUG_RE.fullmatch(trip_type["id"]) is not None,
                "travel.trip_type_id",
                "Trip-type ID must be a lowercase slug",
                path=f"{path}.id",
            )
            validate_bilingual_text_fields(audit, trip_type, ("name", "description"), path)
            audit.check(
                trip_type["recommended_path_id"] in learning_path_ids,
                "travel.learning_path_reference",
                f"Unknown recommended learning path: {trip_type['recommended_path_id']!r}",
                path=f"{path}.recommended_path_id",
            )

    checklists = travel["checklists"]
    checklist_array_ok = isinstance(checklists, list)
    audit.check(checklist_array_ok, "travel.checklists_array", "checklists must be an array", path=f"{root_path}.checklists")
    checklist_item_count = 0
    if checklist_array_ok:
        assert isinstance(checklists, list)
        audit.check(
            len(checklists) == 7,
            "travel.checklists_count",
            f"Expected exactly seven checklists; found {len(checklists)}",
            path=f"{root_path}.checklists",
        )
        checklist_ids = [item.get("id") for item in checklists if isinstance(item, dict)]
        duplicates = duplicate_values(checklist_ids)
        audit.check(
            not duplicates and len(checklist_ids) == len(checklists),
            "travel.checklist_ids",
            f"Checklist IDs must be present and unique: {duplicates}",
            path=f"{root_path}.checklists",
            details=duplicates or None,
        )
        for index, checklist in enumerate(checklists):
            path = f"{root_path}.checklists[{index}]"
            if not require_keys(audit, checklist, ("id", "title_he", "title_en", "items_he", "items_en"), path):
                continue
            assert isinstance(checklist, dict)
            audit.check(
                is_nonempty_string(checklist["id"]) and SLUG_RE.fullmatch(checklist["id"]) is not None,
                "travel.checklist_id",
                "Checklist ID must be a lowercase slug",
                path=f"{path}.id",
            )
            validate_bilingual_text_fields(audit, checklist, ("title",), path)
            validate_bilingual_list_fields(
                audit,
                checklist,
                ("items",),
                path,
                expected_items=6,
                every_hebrew_item=True,
            )
            if isinstance(checklist.get("items_he"), list):
                checklist_item_count += len(checklist["items_he"])

    navigation_apps = travel["navigation_apps"]
    navigation_array_ok = isinstance(navigation_apps, list)
    audit.check(
        navigation_array_ok,
        "travel.navigation_apps_array",
        "navigation_apps must be an array",
        path=f"{root_path}.navigation_apps",
    )
    navigation_video_references = 0
    if navigation_array_ok:
        assert isinstance(navigation_apps, list)
        audit.check(
            len(navigation_apps) == 10,
            "travel.navigation_apps_count",
            f"Expected exactly ten navigation comparisons; found {len(navigation_apps)}",
            path=f"{root_path}.navigation_apps",
        )
        names = [item.get("name") for item in navigation_apps if isinstance(item, dict)]
        duplicate_names = duplicate_values(names)
        audit.check(
            not duplicate_names and len(names) == len(navigation_apps),
            "travel.navigation_app_names",
            f"Navigation-app names must be present and unique: {duplicate_names}",
            path=f"{root_path}.navigation_apps",
            details=duplicate_names or None,
        )
        source_urls: list[str] = []
        for index, comparison in enumerate(navigation_apps):
            path = f"{root_path}.navigation_apps[{index}]"
            required = (
                "name",
                "type_he", "type_en",
                "best_for_he", "best_for_en",
                "capabilities_he", "capabilities_en",
                "advantages_he", "advantages_en",
                "limitations_he", "limitations_en",
                "setup_he", "setup_en",
                "caution_he", "caution_en",
                "source_url",
                "video_ids",
            )
            if not require_keys(audit, comparison, required, path):
                continue
            assert isinstance(comparison, dict)
            audit.check(
                is_nonempty_string(comparison["name"]),
                "travel.navigation_app_name",
                "Navigation-app name must be non-empty",
                path=f"{path}.name",
            )
            validate_bilingual_text_fields(audit, comparison, ("type", "best_for", "setup", "caution"), path)
            validate_bilingual_list_fields(audit, comparison, ("capabilities", "advantages", "limitations"), path)
            audit.check(
                valid_https_url(comparison["source_url"]),
                "travel.source_url",
                "source_url must be a valid credential-free HTTPS URL",
                path=f"{path}.source_url",
            )
            if isinstance(comparison["source_url"], str):
                source_urls.append(comparison["source_url"])
            navigation_video_references += validate_travel_video_ids(
                audit,
                comparison["video_ids"],
                internal_ids,
                f"{path}.video_ids",
            )
        duplicate_urls = duplicate_values(source_urls)
        audit.check(
            not duplicate_urls,
            "travel.duplicate_source_url",
            f"Navigation source URLs must be unique: {duplicate_urls}",
            path=f"{root_path}.navigation_apps",
            details=duplicate_urls or None,
        )

    knowledge_guides = travel["knowledge_guides"]
    guide_array_ok = isinstance(knowledge_guides, list)
    audit.check(
        guide_array_ok,
        "travel.knowledge_guides_array",
        "knowledge_guides must be an array",
        path=f"{root_path}.knowledge_guides",
    )
    guide_video_references = 0
    if guide_array_ok:
        assert isinstance(knowledge_guides, list)
        audit.check(
            len(knowledge_guides) == 6,
            "travel.knowledge_guides_count",
            f"Expected exactly six knowledge guides; found {len(knowledge_guides)}",
            path=f"{root_path}.knowledge_guides",
        )
        guide_ids = [item.get("id") for item in knowledge_guides if isinstance(item, dict)]
        duplicate_ids = duplicate_values(guide_ids)
        audit.check(
            not duplicate_ids and len(guide_ids) == len(knowledge_guides),
            "travel.knowledge_guide_ids",
            f"Knowledge-guide IDs must be present and unique: {duplicate_ids}",
            path=f"{root_path}.knowledge_guides",
            details=duplicate_ids or None,
        )
        for index, guide in enumerate(knowledge_guides):
            path = f"{root_path}.knowledge_guides[{index}]"
            required = (
                "id",
                "eyebrow_he", "eyebrow_en",
                "title_he", "title_en",
                "summary_he", "summary_en",
                "best_when_he", "best_when_en",
                "tradeoffs_he", "tradeoffs_en",
                "setup_checks_he", "setup_checks_en",
                "video_ids",
            )
            if not require_keys(audit, guide, required, path):
                continue
            assert isinstance(guide, dict)
            audit.check(
                is_nonempty_string(guide["id"]) and SLUG_RE.fullmatch(guide["id"]) is not None,
                "travel.knowledge_guide_id",
                "Knowledge-guide ID must be a lowercase slug",
                path=f"{path}.id",
            )
            validate_bilingual_text_fields(audit, guide, ("eyebrow", "title", "summary"), path)
            validate_bilingual_list_fields(audit, guide, ("best_when", "tradeoffs", "setup_checks"), path)
            guide_video_references += validate_travel_video_ids(
                audit,
                guide["video_ids"],
                internal_ids,
                f"{path}.video_ids",
            )

    audit.stats.update(
        {
            "travel_trip_types": len(trip_types) if isinstance(trip_types, list) else 0,
            "travel_checklists": len(checklists) if isinstance(checklists, list) else 0,
            "travel_checklist_items_per_language": checklist_item_count,
            "travel_navigation_comparisons": len(navigation_apps) if isinstance(navigation_apps, list) else 0,
            "travel_knowledge_guides": len(knowledge_guides) if isinstance(knowledge_guides, list) else 0,
            "travel_video_references": navigation_video_references + guide_video_references,
        }
    )


def validate_synonyms(audit: ValidationAudit, synonyms: Any) -> None:
    if not require_keys(audit, synonyms, ("version", "updated", "terms"), "data/synonyms.json"):
        return
    audit.check(is_nonempty_string(synonyms["version"]), "synonyms.version", "Version must be non-empty", path="data/synonyms.json.version")
    audit.check(valid_iso_date(synonyms["updated"]), "synonyms.updated", "Updated must be an ISO date", path="data/synonyms.json.updated")
    terms = synonyms["terms"]
    if not audit.check(isinstance(terms, list) and bool(terms), "synonyms.terms", "Terms must be a non-empty array", path="data/synonyms.json.terms"):
        return
    concept_ids = [term.get("concept_id") for term in terms if isinstance(term, dict)]
    duplicates = duplicate_values(concept_ids)
    audit.check(not duplicates, "synonyms.duplicate_concept", f"Duplicate concept IDs: {duplicates}", path="data/synonyms.json.terms", details=duplicates or None)
    for index, term in enumerate(terms):
        term_path = f"data/synonyms.json.terms[{index}]"
        if not require_keys(audit, term, ("concept_id", "preferred_he", "preferred_en", "variants"), term_path):
            continue
        audit.check(is_nonempty_string(term["concept_id"]) and SLUG_RE.fullmatch(term["concept_id"]) is not None, "synonyms.concept_id", "Concept ID must be a lowercase slug", path=f"{term_path}.concept_id")
        audit.check(is_nonempty_string(term["preferred_he"]), "synonyms.preferred", "preferred_he must be non-empty", path=f"{term_path}.preferred_he")
        audit.check(is_nonempty_string(term["preferred_en"]), "synonyms.preferred", "preferred_en must be non-empty", path=f"{term_path}.preferred_en")
        variants = term["variants"]
        valid_variants = isinstance(variants, list) and bool(variants) and all(is_nonempty_string(item) for item in variants)
        audit.check(valid_variants, "synonyms.variants", "Variants must be a non-empty array of strings", path=f"{term_path}.variants")
        if isinstance(variants, list):
            normalized = [item.casefold().strip() for item in variants if isinstance(item, str)]
            duplicate_variants = duplicate_values(normalized)
            audit.check(not duplicate_variants, "synonyms.duplicate_variant", f"Duplicate variants: {duplicate_variants}", path=f"{term_path}.variants", details=duplicate_variants or None)
    audit.stats["synonym_concepts"] = len(terms)


def validate_site_config(audit: ValidationAudit, config: Any, languages: set[str]) -> None:
    keys = (
        "site_name_he",
        "meta_title_he",
        "meta_description_he",
        "og_title_he",
        "og_description_he",
        "release_version",
        "author_name",
        "community_name",
        "contact",
        "logo_path",
        "safety_warning_he",
        "default_language",
        "direction",
    )
    if not require_keys(audit, config, keys, "data/site-config.json"):
        return
    audit.check(has_hebrew(config["site_name_he"]), "config.site_name", "Site name must contain Hebrew", path="data/site-config.json.site_name_he")
    for key in ("meta_title_he", "meta_description_he", "og_title_he", "og_description_he"):
        audit.check(has_hebrew(config[key]), "config.metadata", f"{key} must contain Hebrew text", path=f"data/site-config.json.{key}")
    audit.check(
        is_nonempty_string(config["release_version"]) and SEMVER_RE.fullmatch(config["release_version"]) is not None,
        "config.release_version",
        "Release version must be a semantic version such as 3.0.0",
        path="data/site-config.json.release_version",
    )
    for key in ("author_name", "community_name", "contact", "logo_path"):
        audit.check(isinstance(config[key], str), "config.optional_string", f"{key} must be a string (empty is allowed)", path=f"data/site-config.json.{key}")
    audit.check(has_hebrew(config["safety_warning_he"]), "config.safety_warning", "Safety warning must contain Hebrew text", path="data/site-config.json.safety_warning_he")
    audit.check(config["default_language"] in languages, "config.language", "Default language must exist in taxonomy", path="data/site-config.json.default_language")
    audit.check(config["direction"] == "rtl", "config.direction", "The Hebrew V1 interface must use rtl", path="data/site-config.json.direction")


def run_validation(
    root: Path = ROOT,
    *,
    expected_count: int | None = None,
    minimum_count: int | None = None,
) -> dict[str, Any]:
    validate_count_options(expected_count, minimum_count)
    audit = ValidationAudit()
    files = {name: root / path.relative_to(ROOT) for name, path in DATA_FILES.items()}
    loaded = {name: load_json(path, audit, str(path.relative_to(root)).replace("\\", "/")) for name, path in files.items()}
    taxonomy_allowed = validate_taxonomy(audit, loaded["taxonomy"])
    long_videos = loaded["videos"] if isinstance(loaded["videos"], list) else []
    short_videos = loaded["shorts"] if isinstance(loaded["shorts"], list) else []
    all_videos = long_videos + short_videos
    validate_domain_category_map(audit, loaded["taxonomy"], all_videos, taxonomy_allowed)
    validate_video_schema(audit, loaded["video_schema"], all_videos)
    internal_ids = validate_videos(
        audit,
        all_videos,
        taxonomy_allowed,
    )
    audit.check(bool(long_videos), "videos.nonempty", "videos.json must contain at least one video", path="data/videos.json")
    if expected_count is not None:
        audit.check(
            len(long_videos) == expected_count,
            "videos.expected_count",
            f"Expected exactly {expected_count} videos; found {len(long_videos)}",
            path="data/videos.json",
        )
    elif minimum_count is not None:
        audit.check(
            len(long_videos) >= minimum_count,
            "videos.minimum_count",
            f"Expected at least {minimum_count} videos; found {len(long_videos)}",
            path="data/videos.json",
        )
    validate_learning_paths(audit, loaded["learning_paths"], internal_ids, taxonomy_allowed["skill_levels"], taxonomy_allowed["risk_levels"])
    learning_path_ids = {
        item.get("id")
        for item in loaded["learning_paths"] or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(loaded["learning_paths"], list) else set()
    validate_travel_guides(audit, loaded["travel_guides"], internal_ids, learning_path_ids)
    validate_synonyms(audit, loaded["synonyms"])
    validate_site_config(audit, loaded["site_config"], taxonomy_allowed["languages"])
    placeholder_hits: list[dict[str, str]] = []
    for label in ("videos", "shorts", "taxonomy", "learning_paths", "travel_guides", "synonyms", "site_config"):
        for value_path, text in walk_strings(loaded[label], f"data.{label}"):
            match = PLACEHOLDER_RE.search(text)
            if match:
                placeholder_hits.append({"path": value_path, "match": match.group(0)})
    audit.check(not placeholder_hits, "content.placeholder", "Placeholder-like content was found", path="data", details=placeholder_hits or None)
    videos = long_videos
    actual_count = len(videos) if isinstance(loaded["videos"], list) else None
    audit.count_expectation = describe_count_expectation(
        expected_count=expected_count,
        minimum_count=minimum_count,
        actual=actual_count,
    )
    audit.stats.update(
        {
            "videos": len(videos),
            "unique_internal_ids": len({item.get("id") for item in videos if isinstance(item, dict)}),
            "unique_youtube_video_ids": len({item.get("youtube_video_id") for item in videos if isinstance(item, dict)}),
            "shorts": len(short_videos),
            "catalogue_total": len(all_videos),
            "catalogue_unique_internal_ids": len({item.get("id") for item in all_videos if isinstance(item, dict)}),
            "catalogue_unique_youtube_video_ids": len({item.get("youtube_video_id") for item in all_videos if isinstance(item, dict)}),
            "taxonomy_categories": len(taxonomy_allowed["categories"]),
            "taxonomy_tags": len(taxonomy_allowed["controlled_tags"]),
        }
    )
    return audit.as_dict()


def write_json_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the complete machine-readable result to stdout")
    parser.add_argument("--report", type=Path, help="Also write the machine-readable JSON result to this path")
    count_group = parser.add_mutually_exclusive_group()
    count_group.add_argument("--expected-count", type=positive_int, help="Require exactly this many videos")
    count_group.add_argument("--minimum-count", type=positive_int, help="Require at least this many videos")
    args = parser.parse_args(argv)
    result = run_validation(
        expected_count=args.expected_count,
        minimum_count=args.minimum_count,
    )
    if args.report:
        write_json_report(args.report, result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['status'].upper()}: validate_data")
        print(f"Checks passed: {result['checks_passed']}")
        print(f"Checks failed: {result['checks_failed']}")
        print(f"Warnings: {len(result['warnings'])}")
        expectation = result["count_expectation"]
        requested = "none" if expectation["mode"] == "none" else f"{expectation['mode']}={expectation['value']}"
        satisfied = "yes" if expectation["satisfied"] else "no"
        print(f"Count expectation: {requested}; actual={expectation['actual']}; satisfied={satisfied}")
        print("Stats: " + ", ".join(f"{key}={value}" for key, value in result["stats"].items()))
        for issue in result["errors"]:
            location = f" ({issue['path']})" if issue.get("path") else ""
            print(f"ERROR [{issue['code']}]{location}: {issue['message']}", file=sys.stderr)
        for warning in result["warnings"]:
            location = f" ({warning['path']})" if warning.get("path") else ""
            print(f"WARNING [{warning['code']}]{location}: {warning['message']}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
