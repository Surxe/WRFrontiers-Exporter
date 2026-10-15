import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from batch_export import run_batch_export
from batch_export.run_batch_export import BatchExporter, MapExporter


class TestExportCommands(unittest.TestCase):
    """The asset and map exports share the game/pak/mapper arguments and differ in mode."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.options = SimpleNamespace(
            steam_game_download_dir=os.path.join(self.test_dir, "steam"),
            output_data_dir=os.path.join(self.test_dir, "exports"),
            output_maps_dir=os.path.join(self.test_dir, "maps"),
            log_level="INFO",
            should_export_textures=False,
            force_export_maps=False,
        )
        os.makedirs(self.options.steam_game_download_dir)
        self.mapper_file = os.path.join(self.test_dir, "mapper.usmap")
        self.validate = patch.object(BatchExporter, "_validate_setup").start()
        patch.object(run_batch_export, "map_filters", return_value=["Sparrow/Maps/Mont/Mont", "Sparrow/Maps/EM1/EM1"]).start()

    def tearDown(self):
        patch.stopall()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _arg(self, command, name):
        return command[command.index(name) + 1]

    def test_asset_command(self):
        command = BatchExporter(self.options, self.mapper_file).command
        self.assertEqual(self._arg(command, "--export-output-path"), self.options.output_data_dir)
        self.assertEqual(self._arg(command, "--should-export-textures"), "false")
        self.assertNotIn("--export-mode", command)

    def test_map_command(self):
        command = MapExporter(self.options, self.mapper_file).command
        self.assertEqual(self._arg(command, "--preset"), "WarRobotsFrontiers")
        self.assertEqual(self._arg(command, "--pak-files-directory"), self.options.steam_game_download_dir)
        self.assertEqual(self._arg(command, "--mapping-file-path"), self.mapper_file)
        self.assertEqual(self._arg(command, "--export-output-path"), self.options.output_maps_dir)
        self.assertEqual(self._arg(command, "--export-mode"), "Maps")
        self.assertEqual(self._arg(command, "--map-filters"), "Sparrow/Maps/Mont/Mont,Sparrow/Maps/EM1/EM1")
        self.assertNotIn("--should-export-textures", command)

    @patch("batch_export.run_batch_export.shutil.which", return_value="/usr/bin/systemd-run")
    @patch("batch_export.run_batch_export.platform.system", return_value="Linux")
    def test_map_command_capped_on_linux(self, _system, _which):
        exporter = MapExporter(self.options, self.mapper_file)
        wrapped = exporter._wrap_command()
        self.assertEqual(wrapped[:4], ["systemd-run", "--user", "--scope", "--quiet"])
        self.assertIn("MemoryMax=2G", wrapped)
        self.assertIn("MemorySwapMax=0", wrapped)
        self.assertEqual(wrapped[wrapped.index("--") + 1:], exporter.command)

    @patch("batch_export.run_batch_export.shutil.which", return_value=None)
    @patch("batch_export.run_batch_export.platform.system", return_value="Linux")
    def test_map_command_uncapped_without_systemd_run(self, _system, _which):
        exporter = MapExporter(self.options, self.mapper_file)
        self.assertEqual(exporter._wrap_command(), exporter.command)

    def test_main_maps_skips_existing_output(self):
        os.makedirs(self.options.output_maps_dir)
        open(os.path.join(self.options.output_maps_dir, "scene.json"), "w").close()
        with patch.object(MapExporter, "run") as run:
            self.assertTrue(run_batch_export.main_maps(self.options, self.mapper_file))
            run.assert_not_called()

    def test_main_maps_forced_reexports(self):
        os.makedirs(self.options.output_maps_dir)
        open(os.path.join(self.options.output_maps_dir, "scene.json"), "w").close()
        self.options.force_export_maps = True
        with patch.object(MapExporter, "run") as run:
            self.assertTrue(run_batch_export.main_maps(self.options, self.mapper_file))
            run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
