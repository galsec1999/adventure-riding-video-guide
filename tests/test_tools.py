from __future__ import annotations

import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tools import (
    build_audit,
    check_links,
    serve_acceptance_fixture,
    validate_data,
    validate_wave1,
)
from tools.fixture_factory import load_json, materialize_project_fixture


SOURCE_VIDEOS = load_json(validate_data.ROOT / "data" / "videos.json")
SOURCE_COUNT = len(SOURCE_VIDEOS)


class MaintenanceToolsTests(unittest.TestCase):
    def test_complete_data_validation_is_nonempty_and_count_agnostic_by_default(self) -> None:
        result = validate_data.run_validation()
        self.assertEqual("pass", result["status"], result["errors"])
        self.assertGreater(result["stats"]["videos"], 0)
        self.assertEqual(SOURCE_COUNT, result["stats"]["videos"])
        self.assertEqual(
            {
                "mode": "none",
                "value": None,
                "actual": SOURCE_COUNT,
                "satisfied": True,
            },
            result["count_expectation"],
        )

    def test_empty_dataset_fails_default_nonempty_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            materialize_project_fixture(validate_data.ROOT, root, SOURCE_COUNT)
            (root / "data" / "videos.json").write_text("[]\n", encoding="utf-8")
            result = validate_data.run_validation(root)
        self.assertEqual("fail", result["status"])
        self.assertIn("videos.nonempty", {error["code"] for error in result["errors"]})
        self.assertEqual(0, result["count_expectation"]["actual"])
        self.assertFalse(result["count_expectation"]["satisfied"])

    def test_expected_and_minimum_count_policies_pass_and_fail_explicitly(self) -> None:
        expected = validate_data.run_validation(expected_count=SOURCE_COUNT)
        minimum = validate_data.run_validation(minimum_count=SOURCE_COUNT)
        expected_mismatch = validate_data.run_validation(expected_count=SOURCE_COUNT + 1)
        minimum_mismatch = validate_data.run_validation(minimum_count=SOURCE_COUNT + 1)

        self.assertEqual("pass", expected["status"], expected["errors"])
        self.assertEqual("expected", expected["count_expectation"]["mode"])
        self.assertEqual("pass", minimum["status"], minimum["errors"])
        self.assertEqual("minimum", minimum["count_expectation"]["mode"])
        self.assertEqual("fail", expected_mismatch["status"])
        self.assertIn("videos.expected_count", {error["code"] for error in expected_mismatch["errors"]})
        self.assertEqual("fail", minimum_mismatch["status"])
        self.assertIn("videos.minimum_count", {error["code"] for error in minimum_mismatch["errors"]})
        self.assertEqual(SOURCE_COUNT, minimum_mismatch["stats"]["videos"])

    def test_count_policies_are_mutually_exclusive_for_api_and_cli(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be used together"):
            validate_data.run_validation(expected_count=SOURCE_COUNT, minimum_count=SOURCE_COUNT)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            validate_data.run_validation(expected_count=0)

        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            validate_data.main(
                [
                    "--expected-count",
                    str(SOURCE_COUNT),
                    "--minimum-count",
                    str(SOURCE_COUNT),
                ]
            )
        self.assertEqual(2, raised.exception.code)
        self.assertIn("not allowed with argument", stderr.getvalue())

    def test_json_console_and_report_document_active_count_expectation(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = validate_data.main(["--expected-count", str(SOURCE_COUNT), "--json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual("expected", payload["count_expectation"]["mode"])
        self.assertEqual(SOURCE_COUNT, payload["count_expectation"]["value"])
        self.assertTrue(payload["count_expectation"]["satisfied"])

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "validation.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = validate_data.main(
                    [
                        "--minimum-count",
                        str(SOURCE_COUNT),
                        "--report",
                        str(report_path),
                    ]
                )
            report = load_json(report_path)
        self.assertEqual(0, exit_code)
        self.assertIn(
            f"Count expectation: minimum={SOURCE_COUNT}; actual={SOURCE_COUNT}; satisfied=yes",
            stdout.getvalue(),
        )
        self.assertEqual("minimum", report["count_expectation"]["mode"])

    def test_legacy_wave1_wrapper_requires_an_explicit_count_and_delegates(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            validate_wave1.main([])
        self.assertEqual(2, raised.exception.code)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = validate_wave1.main(["--expected-count", str(SOURCE_COUNT), "--json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual(SOURCE_COUNT, payload["count_expectation"]["actual"])
        self.assertIn("legacy phase-specific wrapper", stderr.getvalue())

    def test_validator_accepts_temporary_130_and_300_record_fixtures(self) -> None:
        for target_count in (130, 300):
            with self.subTest(target_count=target_count), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                materialize_project_fixture(validate_data.ROOT, root, target_count)
                started_at = time.perf_counter()
                result = validate_data.run_validation(root, expected_count=target_count)
                elapsed_ms = (time.perf_counter() - started_at) * 1_000
                print(
                    f"validator fixture {target_count}: {elapsed_ms:.2f} ms "
                    "(measurement only; no hardware threshold)"
                )
                self.assertEqual("pass", result["status"], result["errors"])
                self.assertEqual(target_count, result["stats"]["videos"])
                self.assertEqual(target_count, result["stats"]["unique_internal_ids"])
                self.assertEqual(target_count, result["stats"]["unique_youtube_video_ids"])

    def test_300_record_fixture_satisfies_minimum_200_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            materialize_project_fixture(validate_data.ROOT, root, 300)
            result = validate_data.run_validation(root, minimum_count=200)
        self.assertEqual("pass", result["status"], result["errors"])
        self.assertEqual(
            {"mode": "minimum", "value": 200, "actual": 300, "satisfied": True},
            result["count_expectation"],
        )

    def test_acceptance_fixture_site_is_ephemeral_and_supports_custom_config(self) -> None:
        production_logo = validate_data.ROOT / "assets" / "acceptance-fixture-logo.svg"
        self.assertFalse(production_logo.exists())
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            serve_acceptance_fixture.prepare_site(root, 130, "custom-logo")
            videos = load_json(root / "data" / "videos.json")
            config = load_json(root / "data" / "site-config.json")
            self.assertEqual(130, len(videos))
            self.assertEqual(130, len({video["id"] for video in videos}))
            self.assertEqual("מדריך בדיקת תצורה", config["site_name_he"])
            self.assertEqual("קהילת בדיקות מקומית", config["community_name"])
            self.assertEqual("assets/acceptance-fixture-logo.svg", config["logo_path"])
            self.assertTrue((root / config["logo_path"]).is_file())
        self.assertFalse(production_logo.exists())

    def test_site_config_allows_empty_optional_identity_fields(self) -> None:
        config = load_json(validate_data.ROOT / "data" / "site-config.json")
        config.update(
            {
                "author_name": "",
                "community_name": "",
                "contact": "",
                "logo_path": "",
            }
        )
        audit = validate_data.ValidationAudit()
        validate_data.validate_site_config(audit, config, {"he", "en"})
        self.assertEqual(0, audit.checks_failed, audit.errors)

    def test_link_checker_is_local_by_default_and_uses_source_count(self) -> None:
        videos = check_links.load_videos()
        report = check_links.build_report(videos)
        self.assertEqual("dry_run_local_only", report["mode"])
        self.assertFalse(report["network_performed"])
        self.assertEqual(len(videos), report["summary"]["local_valid"])
        self.assertEqual(0, report["summary"]["local_invalid"])

    def test_audit_matches_source_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_audit.build_audit(Path(temp_dir))
        self.assertEqual(SOURCE_COUNT, report["total_videos"])
        self.assertEqual(report["total_videos"], report["unique_youtube_video_ids"])
        self.assertGreaterEqual(report["learning_paths"]["count"], 2)
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
