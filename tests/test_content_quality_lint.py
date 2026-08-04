from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import content_quality_lint


def sample_video(record_id: str, youtube_id: str) -> dict:
    return {
        "id": record_id,
        "youtube_video_id": youtube_id,
        "language": "en",
        "channel_name": f"Channel {record_id}",
        "summary_he": " ".join(["סיכום"] * 50),
        "why_watch_he": "הסבר ייחודי ומבוסס ראיות שמבהיר מה בדיוק ניתן ללמוד מן המקור הזה.",
        "fit_for_he": "מיועד לרוכב עם שליטה בסיסית המבקש לתרגל בסביבה סגורה ובהתקדמות מדורגת.",
        "quality_reason_he": "הציון נשען על הדגמה מזוהה ועל התאמה ישירה בין ההסבר לבין נושא הרשומה.",
        "learning_points_he": ["נקודת למידה ייחודית"],
        "exercises_he": ["תרגיל ייחודי בסביבה סגורה"],
        "equipment_he": ["קסדה"],
        "safety_warnings_he": ["יש להשתמש במיגון מלא"],
        "common_mistakes_he": ["טעות ייחודית"],
        "risk_level": "medium",
        "chapters": [],
        "related_video_ids": ["yt-related"],
        "verification": {
            "content_evidence_types": ["description", "transcript"],
            "classification_confidence": "high",
        },
    }


class ContentQualityLintTests(unittest.TestCase):
    def test_run_audit_is_read_only_and_records_matching_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            videos_path = Path(temp_dir) / "videos.json"
            videos_path.write_text(
                json.dumps([sample_video("yt-one", "one")], ensure_ascii=False),
                encoding="utf-8",
            )
            before = videos_path.read_bytes()
            report = content_quality_lint.run_audit(videos_path, None)
            after = videos_path.read_bytes()
        self.assertEqual(before, after)
        self.assertTrue(report["source"]["unchanged"])
        self.assertEqual(
            report["source"]["videos_sha256_before"],
            report["source"]["videos_sha256_after"],
        )

    def test_detects_unsupported_language_description_only_and_low_confidence(self) -> None:
        video = sample_video("yt-one", "one")
        video["language"] = "ja"
        video["verification"] = {
            "content_evidence_types": ["description"],
            "classification_confidence": "low",
        }
        report = content_quality_lint.audit_dataset([video], None)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertEqual("fail", report["status"])
        self.assertIn("language.unsupported", codes)
        self.assertIn("evidence.description_only", codes)
        self.assertIn("evidence.low_confidence", codes)

    def test_detects_high_risk_without_transcript_or_visual_review(self) -> None:
        video = sample_video("yt-one", "one")
        video["risk_level"] = "high"
        video["verification"]["content_evidence_types"] = ["description", "chapters"]
        report = content_quality_lint.audit_dataset([video], None)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("evidence.high_risk_insufficient", codes)

    def test_detects_quarantined_wave1_template_family(self) -> None:
        video = sample_video("yt-one", "one")
        video["learning_points_he"] = ["נקודה א", "נקודה ב", "נקודה ג"]
        video["why_watch_he"] = (
            "הסרטון מחבר בין נקודה א לבין נקודה ב, ומבהיר גם נקודה ג בלי לדלג על רצף הפעולות."
        )
        report = content_quality_lint.audit_dataset([video], None)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("legacy.wave1_why_watch_template", codes)

    def test_detects_exact_and_near_duplicates(self) -> None:
        first = sample_video("yt-one", "one")
        second = sample_video("yt-two", "two")
        repeated = "טקסט מפורט שחוזר בדיוק בשתי רשומות ולכן חייב להגיע לתור הביקורת הידנית"
        first["why_watch_he"] = repeated
        second["why_watch_he"] = repeated
        first["summary_he"] = " ".join(["סיכום"] * 49 + ["אחד"])
        second["summary_he"] = " ".join(["סיכום"] * 49 + ["שניים"])
        report = content_quality_lint.audit_dataset([first, second], None)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("text.exact_duplicate", codes)
        self.assertIn("text.near_duplicate", codes)

    def test_html_escapes_finding_content(self) -> None:
        video = sample_video("yt-<one>", "one")
        video["language"] = "<script>"
        report = content_quality_lint.audit_dataset([video], None)
        rendered = content_quality_lint.render_html(report)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)


if __name__ == "__main__":
    unittest.main()
