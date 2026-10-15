import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from batch_export.map_list import (MAP_NAMES_FILE, QUEUE_COMMON_DATA_FILE, map_filters, map_keys,
                                   queued_map_keys)


def _localized(key):
    return {"Key": key, "Value": {"TableId": "/Game/Sparrow/Localization/ST_MapNames.ST_MapNames",
                                  "Key": f"Map_{key}", "SourceString": key, "LocalizedString": key}}


class TestMapList(unittest.TestCase):
    """The map list comes from the game's own lists in the asset export."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write(self, relative_file, data):
        file = os.path.join(self.test_dir, relative_file)
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file)

    def _write_queue(self, keys):
        self._write(QUEUE_COMMON_DATA_FILE, [{
            "Type": "SQueueModesCommonDataAsset",
            "Properties": {"MapsLocalization": [_localized(key) for key in keys], "GameModesLocalization": []},
        }])

    def _write_names(self, keys):
        self._write(MAP_NAMES_FILE, [{
            "Type": "StringTable",
            "StringTable": {"TableNamespace": "MapNames",
                            "KeysToEntries": {f"Map_{key}": key for key in keys} | {"Other_Key": "x"}},
        }])

    def test_map_keys_queued_then_named_then_firing_range(self):
        self._write_queue(["CrashSite", "Mont"])
        self._write_names(["CrashSite", "Tutorial", "Mont"])
        self.assertEqual(map_keys(self.test_dir), ["CrashSite", "Mont", "Tutorial", "FiringRange"])

    def test_map_keys_without_name_table(self):
        self._write_queue(["EM1"])
        self.assertEqual(map_keys(self.test_dir), ["EM1", "FiringRange"])

    def test_map_filters_are_persistent_levels(self):
        self._write_queue(["Mont"])
        self.assertEqual(map_filters(self.test_dir), ["Sparrow/Maps/Mont/Mont", "Sparrow/Maps/FiringRange/FiringRange"])

    def test_missing_asset_raises(self):
        with self.assertRaises(FileNotFoundError):
            queued_map_keys(self.test_dir)

    def test_empty_list_raises(self):
        self._write_queue([])
        with self.assertRaises(ValueError):
            queued_map_keys(self.test_dir)


if __name__ == '__main__':
    unittest.main()
