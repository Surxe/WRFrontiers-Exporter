import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from batch_export import run_batch_export
from batch_export.run_batch_export import BatchExporter, parse_memory_size


class TestExportCommand(unittest.TestCase):
    """The export runs WRFrontiersDB-CUE4Parse with three paths, under a memory cap."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.options = SimpleNamespace(
            steam_game_download_dir=os.path.join(self.test_dir, "steam"),
            output_data_dir=os.path.join(self.test_dir, "exports"),
            batch_export_memory_max="1536M",
            log_level="INFO",
        )
        self.mapper_file = os.path.join(self.test_dir, "mapper.usmap")
        patch.object(BatchExporter, "_validate_setup").start()

    def tearDown(self):
        patch.stopall()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _exporter(self, system="Linux", systemd_run="/usr/bin/systemd-run"):
        with patch.object(run_batch_export.platform, "system", return_value=system), \
             patch.object(run_batch_export.shutil, "which", return_value=systemd_run):
            return BatchExporter(self.options, self.mapper_file)

    def _export_args(self, command):
        return command[command.index(str(self._exporter().executable_path)):]

    def test_export_arguments(self):
        args = self._export_args(self._exporter().command)
        self.assertEqual(args[1:], [
            "--pak-files-directory", self.options.steam_game_download_dir,
            "--export-output-path", self.options.output_data_dir,
            "--mapping-file-path", self.mapper_file,
        ])

    def test_linux_runs_in_a_capped_scope(self):
        exporter = self._exporter()
        separator = exporter.command.index("--")
        self.assertEqual(exporter.command[:4], ["systemd-run", "--user", "--scope", "--quiet"])
        self.assertIn("MemoryMax=1536M", exporter.command[:separator])
        self.assertIn("MemorySwapMax=0", exporter.command[:separator])
        self.assertEqual(exporter.command[separator + 1], str(exporter.executable_path))
        self.assertIn("XDG_RUNTIME_DIR", exporter.env)
        self.assertNotIn("DOTNET_GCHeapHardLimit", exporter.env)
        self.assertNotIn("LD_LIBRARY_PATH", exporter.env.keys() - os.environ.keys())

    def test_without_systemd_sets_the_gc_heap_limit(self):
        for system, systemd_run in [("Windows", None), ("Linux", None)]:
            exporter = self._exporter(system, systemd_run)
            self.assertEqual(exporter.command[0], str(exporter.executable_path))
            # 75% of 1536 MiB, the same budget .NET derives from a cgroup MemoryMax
            self.assertEqual(exporter.env["DOTNET_GCHeapHardLimit"], hex(1152 * 1024 * 1024))

    def test_scope_none_skips_systemd_even_when_available(self):
        # A container has systemd-run on the PATH but no user session bus.
        self.options.batch_export_memory_scope = "none"
        exporter = self._exporter()
        self.assertEqual(exporter.command[0], str(exporter.executable_path))
        self.assertEqual(exporter.env["DOTNET_GCHeapHardLimit"], hex(1152 * 1024 * 1024))

    def test_scope_systemd_uses_the_scope(self):
        self.options.batch_export_memory_scope = "systemd"
        exporter = self._exporter()
        self.assertEqual(exporter.command[:4], ["systemd-run", "--user", "--scope", "--quiet"])

    def test_scope_systemd_fails_without_systemd_run(self):
        self.options.batch_export_memory_scope = "systemd"
        for system, systemd_run in [("Windows", None), ("Linux", None)]:
            with self.assertRaises(RuntimeError):
                self._exporter(system, systemd_run)

    def test_scope_auto_is_the_default(self):
        self.options.batch_export_memory_scope = "auto"
        self.assertEqual(self._exporter().command[0], "systemd-run")
        exporter = self._exporter("Linux", None)
        self.assertEqual(exporter.command[0], str(exporter.executable_path))

    def test_unknown_scope_is_rejected(self):
        self.options.batch_export_memory_scope = "cgroup"
        with self.assertRaises(ValueError):
            self._exporter()

    def test_exit_codes_are_explained(self):
        exporter = self._exporter()
        self.assertIn("ran out of memory", exporter.describe_exit(3))
        self.assertIn("killed", exporter.describe_exit(-9))
        self.assertIn("killed", exporter.describe_exit(137))
        self.assertIn("export failures", exporter.describe_exit(1))
        self.assertIn("exit code 2", exporter.describe_exit(2))


class TestParseMemorySize(unittest.TestCase):

    def test_sizes(self):
        self.assertEqual(parse_memory_size("1536M"), 1536 * 1024 ** 2)
        self.assertEqual(parse_memory_size("2g"), 2 * 1024 ** 3)
        self.assertEqual(parse_memory_size("512K"), 512 * 1024)
        self.assertEqual(parse_memory_size("805306368"), 805306368)

    def test_invalid(self):
        for value in ["", "1.5G", "lots", "-1M", "1536MB"]:
            with self.assertRaises(ValueError):
                parse_memory_size(value)


if __name__ == "__main__":
    unittest.main()
