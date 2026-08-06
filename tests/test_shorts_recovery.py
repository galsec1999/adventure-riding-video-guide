"""Regression tests for Shorts recovery source triage. Document version 1.1.0."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from recover_shorts_content import classify_source  # noqa: E402


def info(title: str, description: str, *, duration: int = 45) -> dict:
    return {
        "title": title,
        "description": description,
        "duration": duration,
        "availability": "public",
        "uploader": "Test Training Channel",
    }


class ShortsRecoveryTests(unittest.TestCase):
    def test_production_selection_matches_the_individual_review_ledger(self) -> None:
        shorts = json.loads((ROOT / "data/shorts.json").read_text(encoding="utf-8"))
        source = json.loads((ROOT / "research/shorts-v3.3/source-audit.json").read_text(encoding="utf-8"))
        visual = json.loads((ROOT / "research/shorts-v3.3/visual-review.json").read_text(encoding="utf-8"))
        source_by_id = {item["youtube_video_id"]: item for item in source["items"]}
        published_ids = {item["youtube_video_id"] for item in shorts}
        reviewed_kept = {item["youtube_video_id"] for item in visual["items"] if item["decision"] == "keep"}
        self.assertEqual(len(shorts), 152)
        self.assertEqual(visual["reviewed_count"], 180)
        self.assertEqual(published_ids, reviewed_kept)
        self.assertNotIn("ExTiVb7J63Q", published_ids)
        self.assertNotIn("OFIKN7CtR9U", published_ids)
        self.assertNotIn("wGP_yyis-d4", published_ids)
        for video_id in published_ids:
            self.assertFalse(source_by_id[video_id]["title_sales_markers"])
            self.assertFalse(source_by_id[video_id]["caption_sales_markers"])

    def test_public_caption_can_support_real_navigation(self) -> None:
        record = {
            "youtube_video_id": "nav-test",
            "published_title": "Import a GPX route into Garmin",
            "published_category": "route_navigation",
        }
        result = classify_source(
            record,
            info(
                "Import a GPX route into Garmin",
                "A short route navigation lesson for adventure riders.",
            ),
            "Open the GPX file, select the route, then import the GPX route into the Garmin navigation unit.",
            "en",
        )
        self.assertEqual(result["preliminary_decision"], "candidate")
        self.assertEqual(result["proposed_category"], "route_navigation")

    def test_gps_tire_can_never_recover_as_navigation(self) -> None:
        record = {
            "youtube_video_id": "tire-test",
            "published_title": "Motoz Tractionator GPS Tire",
            "published_category": "route_navigation",
        }
        result = classify_source(
            record,
            info(
                "Motoz Tractionator GPS Tire",
                "A motorcycle tire review for our rental fleet.",
            ),
            "This GPS tire has a reversible tread pattern for motorcycle travel.",
            "en",
        )
        self.assertEqual(result["preliminary_decision"], "remove")
        self.assertEqual(result["reason"], "known_false_semantic_match")

    def test_channel_boilerplate_does_not_replace_content_review(self) -> None:
        record = {
            "youtube_video_id": "uturn-test",
            "published_title": "How to practice motorcycle U-turns",
            "published_category": "u_turns_low_speed",
        }
        result = classify_source(
            record,
            info(
                "How to practice motorcycle U-turns",
                "A U-turn practice lesson. Follow the channel and visit the link in bio for more training.",
            ),
            "Use the friction zone and rear brake during the motorcycle U-turn. Look through the turn and practice both directions.",
            "en",
        )
        self.assertEqual(result["preliminary_decision"], "candidate")
        self.assertTrue(result["description_marketing_markers"])

    def test_sales_focused_title_is_removed(self) -> None:
        record = {
            "youtube_video_id": "sale-test",
            "published_title": "Buy now: motorcycle tire sale",
            "published_category": "tires_setup",
        }
        result = classify_source(
            record,
            info(
                "Buy now: motorcycle tire sale",
                "Motorcycle tires are in stock with free shipping.",
            ),
            "Order yours today.",
            "en",
        )
        self.assertEqual(result["preliminary_decision"], "remove")
        self.assertEqual(result["reason"], "commercial_content_focus")

    def test_old_category_does_not_override_stronger_live_evidence(self) -> None:
        record = {
            "youtube_video_id": "corner-test",
            "published_title": "How to ride through downhill corners",
            "published_category": "descents",
        }
        result = classify_source(
            record,
            info(
                "How to ride through downhill corners",
                "A road cornering lesson about line choice through downhill corners.",
            ),
            "In a downhill corner, choose the corner entry and look through the corner before the apex.",
            "en",
        )
        self.assertEqual(result["preliminary_decision"], "candidate")
        self.assertEqual(result["proposed_category"], "road_cornering")


if __name__ == "__main__":
    unittest.main()
