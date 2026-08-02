from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import build_audit, check_links, validate_data


class MaintenanceToolsTests(unittest.TestCase):
    def test_complete_data_validation_passes(self) -> None:
        result = validate_data.run_validation()
        self.assertEqual("pass", result["status"], result["errors"])
        self.assertEqual(60, result["stats"]["videos"])
        self.assertEqual(2, result["stats"]["learning_paths"])

    def test_link_checker_is_local_by_default(self) -> None:
        videos = check_links.load_videos()
        report = check_links.build_report(videos)
        self.assertEqual("dry_run_local_only", report["mode"])
        self.assertFalse(report["network_performed"])
        self.assertEqual(60, report["summary"]["local_valid"])
        self.assertEqual(0, report["summary"]["local_invalid"])

    def test_audit_matches_source_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_audit.build_audit(Path(temp_dir))
        self.assertEqual(60, report["total_videos"])
        self.assertEqual(60, report["unique_youtube_video_ids"])
        self.assertEqual(2, report["learning_paths"]["count"])
        self.assertEqual("pass", report["validation"]["status"])

    def test_audit_writes_all_three_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            report = build_audit.build_audit(output)
            paths = build_audit.write_reports(output, report)
            self.assertEqual({".json", ".csv", ".html"}, {path.suffix for path in paths})
            self.assertTrue(all(path.exists() and path.stat().st_size > 0 for path in paths))


if __name__ == "__main__":
    unittest.main()

