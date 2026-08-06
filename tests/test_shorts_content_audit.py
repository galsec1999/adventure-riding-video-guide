"""Regression tests for the strict Shorts content audit. Document version 1.0.0."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.audit_shorts_content import PROMO_RE, topic_scores  # noqa: E402


class ShortsContentAuditTests(unittest.TestCase):
    def test_tractionator_gps_is_a_tire_not_navigation(self) -> None:
        scores = topic_scores(
            "Motoz Tractionator GPS Tire",
            "A comparison of the Motoz Tractionator GPS tire with another motorcycle tire.",
            "",
        )
        categories = {item["category"] for item in scores}
        self.assertIn("tires_setup", categories)
        self.assertNotIn("route_navigation", categories)

    def test_gpx_motorcycle_model_is_not_navigation(self) -> None:
        scores = topic_scores(
            "Giant log on the GPX TSE 300",
            "Trail obstacle practice on a GPX TSE 300 motorcycle.",
            "",
        )
        self.assertNotIn("route_navigation", {item["category"] for item in scores})

    def test_real_gpx_route_workflow_is_navigation(self) -> None:
        scores = topic_scores(
            "How to import a GPX route into a Garmin Zumo",
            "This route navigation guide shows GPX file import into a GPS navigation unit.",
            "",
        )
        navigation = next(item for item in scores if item["category"] == "route_navigation")
        self.assertTrue(navigation["title_matches"])
        self.assertTrue(navigation["source_supported"])

    def test_commercial_call_to_action_is_rejected(self) -> None:
        self.assertIsNotNone(PROMO_RE.search("Buy now from our rental fleet and use code ADV"))

    def test_production_shorts_all_have_strict_evidence(self) -> None:
        shorts = json.loads((ROOT / "data/shorts.json").read_text(encoding="utf-8"))
        self.assertEqual(len(shorts), 11)
        self.assertNotIn("ExTiVb7J63Q", {item["youtube_video_id"] for item in shorts})
        self.assertNotIn("OFIKN7CtR9U", {item["youtube_video_id"] for item in shorts})
        for item in shorts:
            evidence = set(item["verification"]["content_evidence_types"])
            self.assertTrue({"youtube_player_description", "visual_content_review"}.issubset(evidence))
            self.assertEqual(item["verification"]["classification_confidence"], "high")


if __name__ == "__main__":
    unittest.main()
