import os
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from health_check import check_disk, clean_logs


class CheckDiskTests(unittest.TestCase):
    @patch("health_check.shutil.disk_usage", return_value=(1000, 825, 175))
    def test_reports_warning_above_threshold(self, disk_usage):
        result = check_disk("C:\\", warn_pct=80)

        self.assertEqual(result["mount"], "C:\\")
        self.assertEqual(result["used_pct"], 82.5)
        self.assertEqual(result["free_gib"], 0)
        self.assertEqual(result["status"], "WARN")
        disk_usage.assert_called_once_with("C:\\")

    @patch("health_check.shutil.disk_usage", return_value=(1000, 800, 200))
    def test_threshold_boundary_is_ok(self, disk_usage):
        self.assertEqual(check_disk("/", warn_pct=80)["status"], "OK")


class CleanLogsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_old(self, path):
        old_time = time.time() - 10 * 86400
        os.utime(path, (old_time, old_time))

    def test_dry_run_lists_old_logs_without_removing_them(self):
        old_log = self.folder / "old.log"
        recent_log = self.folder / "recent.log"
        notes = self.folder / "notes.txt"
        old_log.write_text("old", encoding="utf-8")
        recent_log.write_text("recent", encoding="utf-8")
        notes.write_text("keep", encoding="utf-8")
        self.make_old(old_log)

        matched = clean_logs(self.folder, days=7, dry_run=True)

        self.assertEqual(matched, [str(old_log)])
        self.assertTrue(old_log.exists())
        self.assertTrue(recent_log.exists())
        self.assertTrue(notes.exists())

    def test_apply_removes_only_old_log_files(self):
        old_log = self.folder / "old.log"
        recent_log = self.folder / "recent.log"
        notes = self.folder / "notes.txt"
        old_log.write_text("old", encoding="utf-8")
        recent_log.write_text("recent", encoding="utf-8")
        notes.write_text("keep", encoding="utf-8")
        self.make_old(old_log)

        matched = clean_logs(self.folder, days=7, dry_run=False)

        self.assertEqual(matched, [str(old_log)])
        self.assertFalse(old_log.exists())
        self.assertTrue(recent_log.exists())
        self.assertTrue(notes.exists())

    def test_os_error_for_one_file_does_not_crash_cleanup(self):
        blocked_log = self.folder / "blocked.log"
        blocked_log.write_text("blocked", encoding="utf-8")
        output = StringIO()
        original_stat = Path.stat

        def fail_for_blocked_file(path, *args, **kwargs):
            if path == blocked_log:
                raise OSError("permission denied")
            return original_stat(path, *args, **kwargs)

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(Path, "stat", new=fail_for_blocked_file):
                with redirect_stdout(output):
                    matched = clean_logs(self.folder, days=7, dry_run=True)

        self.assertEqual(matched, [])
        self.assertIn("skip", output.getvalue())


if __name__ == "__main__":
    unittest.main()
