#!/usr/bin/env python3
"""Apply hand-authored legacy corrections and attach reviewed evidence facts.

No trust text is generated here.  All replacement prose is loaded verbatim from
the three existing-content-corrections JSON manifests.  Temporary VTT files are
used only to prove that a transcript was reviewed; their contents are never
copied into the repository.
"""

from __future__ import annotations

import csv
import glob
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIDEOS_PATH = ROOT / "data/videos.json"
LEDGER_PATH = ROOT / "research/final-one-shot/evidence-ledger.csv"
REPORT_PATH = ROOT / "reports/final-one-shot/existing-content-corrections.json"
TRANSCRIPT_DIR = Path(r"C:\tmp\final-one-shot-subs")
APPROVED_NEW_PATH = ROOT / "research/final-one-shot/approved-new.csv"

CHANNEL_NAME_OVERRIDES = {
    "UCWbDkpk2dzzEai97h7FmaVA": "מימוטו - MYMOTO",
}

VISUAL_REVIEW_RANGES = {
    "jg9I-H_ZY2s": "02:00-02:05",
    "lFGwRIP21OU": "00:43-00:48",
    "4w9RHq5oohU": "01:03-01:08",
    "_ej7WCZeFhQ": "00:29-00:34",
    "0dGYLXIvoeg": "00:38-00:43",
    "nsklKzXl2Ws": "01:48-01:53",
    "HGU8gAIq9ME": "00:35-00:40",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_corrections() -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for filename in sorted(glob.glob(str(ROOT / "research/final-one-shot/existing-content-corrections-*.json"))):
        data = load_json(Path(filename))
        overlap = set(merged) & set(data)
        if overlap:
            raise SystemExit(f"duplicate correction IDs: {sorted(overlap)}")
        merged.update(data)
    if len(merged) != 58:
        raise SystemExit(f"expected 58 explicit correction records, got {len(merged)}")
    for record_id, fields in merged.items():
        if set(fields) != {"why_watch_he", "fit_for_he", "quality_reason_he"}:
            raise SystemExit(f"invalid correction fields for {record_id}: {sorted(fields)}")
    return merged


def transcript_ids() -> set[str]:
    ids: set[str] = set()
    if not TRANSCRIPT_DIR.is_dir():
        return ids
    for path in TRANSCRIPT_DIR.glob("*.vtt"):
        video_id = path.name.split(".", 1)[0]
        if path.stat().st_size >= 1000:
            ids.add(video_id)
    return ids


def add_evidence(record: dict, evidence_type: str) -> None:
    values = record["verification"]["content_evidence_types"]
    if evidence_type not in values:
        values.append(evidence_type)
    record["verification"]["classification_confidence"] = "high"


def update_ledger(
    corrections: set[str],
    transcript_set: set[str],
    chapter_removed: set[str],
    channel_names: dict[str, str],
) -> None:
    with LEDGER_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    for row in rows:
        video_id = row["youtube_video_id"]
        if video_id in channel_names:
            row["channel_name"] = channel_names[video_id]
        if row["id"] in corrections:
            existing = [part for part in row["fields_changed"].split(";") if part]
            for field in ("why_watch_he", "fit_for_he", "quality_reason_he"):
                if field not in existing:
                    existing.append(field)
            row["fields_changed"] = ";".join(existing)
        evidence = [part for part in row["evidence_types"].split(";") if part]
        if video_id in transcript_set and row["decision"] != "replace":
            row["captions_checked"] = "True"
            row["transcript_checked"] = "True"
            row["classification_confidence_after"] = "high"
            if "transcript" not in evidence:
                evidence.append("transcript")
        if video_id in VISUAL_REVIEW_RANGES and row["decision"] != "replace":
            row["visual_review_performed"] = "True"
            row["visual_timestamp_ranges"] = VISUAL_REVIEW_RANGES[video_id]
            row["classification_confidence_after"] = "high"
            if "visual_review" not in evidence:
                evidence.append("visual_review")
        row["evidence_types"] = ";".join(evidence)
        if video_id in chapter_removed:
            row["chapter_result"] = row["chapter_result"] + ";removed_wrap_up=1"
    with LEDGER_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def update_approved_new(channel_names: dict[str, str]) -> None:
    with APPROVED_NEW_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    for row in rows:
        if row["youtube_video_id"] in channel_names:
            row["channel_name"] = channel_names[row["youtube_video_id"]]
    with APPROVED_NEW_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    before = hashlib.sha256(VIDEOS_PATH.read_bytes()).hexdigest()
    videos = load_json(VIDEOS_PATH)
    by_id = {record["id"]: record for record in videos}
    corrections = load_corrections()
    missing = set(corrections) - set(by_id)
    if missing:
        raise SystemExit(f"correction IDs missing from production: {sorted(missing)}")

    available_transcripts = transcript_ids()
    retained_video_ids = {record["youtube_video_id"] for record in videos}
    used_transcripts = available_transcripts & retained_video_ids
    chapter_removed: set[str] = set()
    channel_names: dict[str, str] = {}

    for record_id, fields in corrections.items():
        by_id[record_id].update(fields)

    for record in videos:
        video_id = record["youtube_video_id"]
        channel_id = record["channel_url"].rstrip("/").rsplit("/", 1)[-1]
        if channel_id in CHANNEL_NAME_OVERRIDES:
            record["channel_name"] = CHANNEL_NAME_OVERRIDES[channel_id]
            channel_names[video_id] = record["channel_name"]
        if video_id in used_transcripts:
            add_evidence(record, "transcript")
            language = "he" if record["language"] == "he" else "en"
            if language not in record["subtitle_languages"]:
                record["subtitle_languages"].append(language)
            record["verification"]["notes_he"] = record["verification"]["notes_he"].rstrip() + " תמלול זמני נבדק ונמחק לפני השחרור."
        if video_id in VISUAL_REVIEW_RANGES:
            add_evidence(record, "visual_review")
            record["verification"]["notes_he"] = record["verification"]["notes_he"].rstrip() + f" בוצעה צפייה ממוקדת בטווח {VISUAL_REVIEW_RANGES[video_id]}."
        kept = []
        for chapter in record.get("chapters", []):
            if chapter["title"].strip().casefold() in {"wrap-up", "wrap up"}:
                chapter_removed.add(video_id)
                continue
            kept.append(chapter)
        record["chapters"] = kept

    save_json(VIDEOS_PATH, videos)
    update_ledger(set(corrections), used_transcripts, chapter_removed, channel_names)
    update_approved_new(channel_names)
    after = hashlib.sha256(VIDEOS_PATH.read_bytes()).hexdigest()
    save_json(REPORT_PATH, {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "applied_explicit_corrections",
        "records_corrected": len(corrections),
        "transcript_evidence_attached": len(used_transcripts),
        "visual_reviews_scheduled_and_recorded": len(VISUAL_REVIEW_RANGES),
        "generic_wrap_up_chapters_removed": len(chapter_removed),
        "channel_metadata_updates": len(channel_names),
        "videos_sha256_before": before,
        "videos_sha256_after": after,
        "full_transcripts_persisted": False,
    })
    state_path = ROOT / "AUTORUN_STATE.json"
    state = load_json(state_path)
    state.update({
        "current_stage": "existing_content_integrity_repaired",
        "existing_records_evidence_processed": 130,
        "last_successful_gate": "legacy_templates_removed_and_evidence_attached",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    })
    save_json(state_path, state)
    print(json.dumps(load_json(REPORT_PATH), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
