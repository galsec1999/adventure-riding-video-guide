"""Unit tests for upgrade_content_schema.py.

Document version: 1.0.0
"""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools import upgrade_content_schema


def fixture_document() -> dict:
    return {
        "title": "Adventure guide fixture",
        "chapters": [
            {
                "number": 9,
                "cards": [
                    {
                        "id": "card-9-10",
                        "number": "9.10",
                        "title": "קופסת נתיכים וריליי לאביזרים",
                        "official_sources": ["O009"],
                    },
                    {
                        "id": "card-9-11",
                        "number": "9.11",
                        "title": "התקנת פנסי ערפל/עזר",
                    },
                ],
            },
            {
                "number": 17,
                "cards": [
                    {
                        "id": "card-17-6",
                        "number": "17.6",
                        "title": "קופסת נתיכים וריליי לאביזרים",
                    },
                    {
                        "id": "card-17-7",
                        "number": "17.7",
                        "title": "פנסי ערפל ופנסי עזר: התקנה וכיוון",
                    },
                ],
            },
        ],
        "videos": [
            {
                "id": "V001",
                "title": "Metadata-screened video",
                "ai_review": {
                    "status": "pre_screened",
                    "basis": "title_description_metadata_and_card_context",
                    "reviewed_on": "2026-08-03",
                    "transcript_required": True,
                },
            },
            {"id": "V002", "title": "Unreviewed video"},
        ],
    }


def card_by_number(document: dict, number: str) -> dict:
    for chapter in document["chapters"]:
        for card in chapter["cards"]:
            if card["number"] == number:
                return card
    raise AssertionError(f"missing card {number}")


class UpgradeContentSchemaTests(unittest.TestCase):
    def test_migration_is_conservative_and_does_not_mutate_input(self) -> None:
        source = fixture_document()
        before = copy.deepcopy(source)

        migrated, report = upgrade_content_schema.migrate_document(source)

        self.assertEqual(before, source)
        self.assertTrue(report["would_change"])
        canonical = card_by_number(migrated, "9.10")
        duplicate = card_by_number(migrated, "17.6")
        self.assertEqual("adventure", canonical["surface_scope"])
        self.assertIsNone(canonical["content_type"])
        self.assertEqual([], canonical["bike_classes"])
        self.assertEqual("needs_review", canonical["content_status"])
        self.assertEqual(["O009"], canonical["official_source_refs"])
        self.assertEqual("card-9-10", duplicate["duplicate_of"])
        self.assertIn("card-17-6", canonical["related_card_ids"])
        self.assertIn("card-9-10", duplicate["related_card_ids"])
        self.assertEqual(4, report["cards_seen"])
        self.assertEqual(2, report["videos_seen"])
        self.assertEqual(
            [{"canonical": "card-9-10", "duplicate": "card-17-6"}],
            report["duplicate_marks"],
        )

    def test_video_review_status_uses_only_explicit_legacy_evidence(self) -> None:
        migrated, _ = upgrade_content_schema.migrate_document(fixture_document())
        screened, unreviewed = migrated["videos"]

        self.assertEqual("metadata_screened", screened["review_status"])
        self.assertEqual("2026-08-03", screened["reviewed_at"])
        self.assertEqual(
            "title_description_metadata_and_card_context",
            screened["evidence_basis"],
        )
        self.assertFalse(screened["transcript_reviewed"])
        self.assertIsNone(screened["view_count"])
        self.assertEqual([], screened["caption_languages"])
        self.assertEqual("unreviewed", unreviewed["review_status"])
        self.assertIsNone(unreviewed["transcript_reviewed"])
        self.assertEqual([], unreviewed["claims_checked"])

    def test_existing_schema_values_are_preserved(self) -> None:
        source = fixture_document()
        card = card_by_number(source, "9.10")
        card.update(
            {
                "content_type": "procedure",
                "surface_scope": "road",
                "content_status": "verified",
                "official_source_refs": ["CUSTOM"],
            }
        )
        source["videos"][0]["review_status"] = "editor_approved"

        migrated, _ = upgrade_content_schema.migrate_document(source)

        migrated_card = card_by_number(migrated, "9.10")
        self.assertEqual("procedure", migrated_card["content_type"])
        self.assertEqual("road", migrated_card["surface_scope"])
        self.assertEqual("verified", migrated_card["content_status"])
        self.assertEqual(["CUSTOM"], migrated_card["official_source_refs"])
        self.assertEqual("editor_approved", migrated["videos"][0]["review_status"])

    def test_migration_is_idempotent(self) -> None:
        first, _ = upgrade_content_schema.migrate_document(fixture_document())
        second, report = upgrade_content_schema.migrate_document(first)

        self.assertEqual(first, second)
        self.assertFalse(report["would_change"])
        self.assertEqual({}, report["card_fields_added"])
        self.assertEqual({}, report["video_fields_added"])
        self.assertEqual(0, report["related_links_added"])

    def test_default_cli_mode_reports_without_modifying_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "guide.json"
            path.write_text(
                json.dumps(fixture_document(), ensure_ascii=False), encoding="utf-8"
            )
            before = path.read_bytes()
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                result = upgrade_content_schema.main(["--input", str(path)])

            report = json.loads(stdout.getvalue())
            self.assertEqual(0, result)
            self.assertEqual("dry-run", report["mode"])
            self.assertTrue(report["would_change"])
            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
