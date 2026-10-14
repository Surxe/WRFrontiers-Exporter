"""
The maps to export, read from the game's own list in the asset export.

The matchmaking screen's DA_QueueCommonData names every map a queue can pick
(``MapsLocalization``, keyed by the map's folder), and ST_MapNames, the string
table those names come from, also names the ones no queue picks (the tutorial).
The firing range has no name in either, so it is added by hand. A map is exported
by its persistent level, the level named after its own folder:
``Sparrow/Maps/<Key>/<Key>``.
"""
import json
import os
from typing import List

QUEUE_COMMON_DATA_FILE = os.path.join(
    "WRFrontiers", "Content", "Sparrow", "UI", "Meta", "QueueModes", "DataAssets", "DA_QueueCommonData.json"
)
MAP_NAMES_FILE = os.path.join("WRFrontiers", "Content", "Sparrow", "Localization", "ST_MapNames.json")
MAP_NAME_KEY_PREFIX = "Map_"
# Played, but named nowhere.
UNNAMED_MAPS = ["FiringRange"]


def _load_json(file: str):
    with open(file, encoding="utf-8") as json_file:
        return json.load(json_file)


def queued_map_keys(output_data_dir: str) -> List[str]:
    """Map folders the matchmaking queues list. Raises if the asset is missing or lists none."""
    file = os.path.join(output_data_dir, QUEUE_COMMON_DATA_FILE)
    if not os.path.isfile(file):
        raise FileNotFoundError(f"Map list asset not found: {file}. Run the asset export (SHOULD_BATCH_EXPORT) first.")
    entries = _load_json(file)
    maps = next((entry.get("Properties", {}).get("MapsLocalization") for entry in entries
                 if entry.get("Type") == "SQueueModesCommonDataAsset"), None)
    keys = [item["Key"] for item in maps or [] if item.get("Key")]
    if not keys:
        raise ValueError(f"No maps in MapsLocalization of {file}")
    return keys


def named_map_keys(output_data_dir: str) -> List[str]:
    """Map folders named in ST_MapNames (``Map_<Key>``); empty if the table is not exported."""
    file = os.path.join(output_data_dir, MAP_NAMES_FILE)
    if not os.path.isfile(file):
        return []
    table = next((entry for entry in _load_json(file) if entry.get("Type") == "StringTable"), {})
    keys = table.get("StringTable", {}).get("KeysToEntries", {})
    return [key[len(MAP_NAME_KEY_PREFIX):] for key in keys if key.startswith(MAP_NAME_KEY_PREFIX)]


def map_keys(output_data_dir: str) -> List[str]:
    """Every released map's folder name: the queued ones first, in the game's order."""
    keys = queued_map_keys(output_data_dir)
    for key in named_map_keys(output_data_dir) + UNNAMED_MAPS:
        if key not in keys:
            keys.append(key)
    return keys


def map_filters(output_data_dir: str) -> List[str]:
    """``--map-filters`` entries: the persistent level of every released map."""
    return [f"Sparrow/Maps/{key}/{key}" for key in map_keys(output_data_dir)]
