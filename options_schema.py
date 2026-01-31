from typing import Literal
from pathlib import Path

"""
# Patterns
* **should_** - Main action flags (e.g., `should_download_steam_game`)
* **force_** - Override/refresh flags (e.g., `force_download_dependencies`)
"""

OPTIONS_SCHEMA = {
    "LOG_LEVEL": {
        "env": "LOG_LEVEL",
        "arg": "--log-level",
        "type": Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "default": "DEBUG",
        "section": "Logging",
        "help": "Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
    },
    "SHOULD_DOWNLOAD_DEPENDENCIES": {
        "env": "SHOULD_DOWNLOAD_DEPENDENCIES",
        "arg": "--should-download-dependencies",
        "type": bool,
        "default": False,
        "help": "Whether to download dependencies.",
        "section": "Dependencies",
    },
    "FORCE_DOWNLOAD_DEPENDENCIES": {
        "env": "FORCE_DOWNLOAD_DEPENDENCIES",
        "arg": "--force-download-dependencies",
        "type": bool,
        "default": False,
        "section": "Dependencies",
        "help": "Re-download dependencies even if they are already present.",
        "depends_on": ["SHOULD_DOWNLOAD_DEPENDENCIES"]
    },
    "SHOULD_DOWNLOAD_STEAM_GAME": {
        "env": "SHOULD_DOWNLOAD_STEAM_GAME",
        "arg": "--should-download-steam-game",
        "type": bool,
        "default": False,
        "help": "Whether to download Steam game files.",
        "section": "Steam Download",
    },
    "FORCE_STEAM_DOWNLOAD": {
        "env": "FORCE_STEAM_DOWNLOAD",
        "arg": "--force-steam-download",
        "type": bool,
        "default": False,
        "help": "Re-download/update Steam game files even if they are already present.",
        "section": "Steam Download",
        "depends_on": ["SHOULD_DOWNLOAD_STEAM_GAME"]
    },
    "MANIFEST_ID": {
        "env": "MANIFEST_ID",
        "arg": "--manifest-id",
        "type": str,
        "default": "latest",
        "help": "Steam manifest ID to download. If 'latest', the latest manifest ID will be used.",
        "links": {"SteamDB": "https://steamdb.info/app/1491000/depot/1491005/manifests/"},
        "section": "Steam Download",
        "depends_on": ["SHOULD_DOWNLOAD_STEAM_GAME"]
    },
    "STEAM_USERNAME": {
        "env": "STEAM_USERNAME",
        "arg": "--steam-username",
        "type": str,
        "default": None,
        "help": "Steam username for authentication.",
        "section": "Steam Download",
        "depends_on": ["SHOULD_DOWNLOAD_STEAM_GAME"],
        "example": "example_user"
    },
    "STEAM_PASSWORD": {
        "env": "STEAM_PASSWORD",
        "arg": "--steam-password",
        "type": str,
        "default": None,
        "sensitive": True,
        "help": "Steam password for authentication.",
        "section": "Steam Download",
        "depends_on": ["SHOULD_DOWNLOAD_STEAM_GAME"],
        "example": "example_password"
    },
    "STEAM_GAME_DOWNLOAD_DIR": {
        "env": "STEAM_GAME_DOWNLOAD_DIR",
        "arg": "--steam-game-download-dir",
        "type": Path,
        "default": None,
        "help": "Path to the local Steam game installation directory.",
        "section": "Steam Download",
        "depends_on": ["SHOULD_DOWNLOAD_STEAM_GAME"],
        "example": Path("C:/WRFrontiersDB/SteamDownload")
    },
    "SHOULD_GET_MAPPER": {
        "env": "SHOULD_GET_MAPPER",
        "arg": "--should-get-mapper",
        "type": bool,
        "default": False,
        "help": "Whether to get the mapping file using Dumper7.",
        "section": "Mapping",
    },
    "FORCE_GET_MAPPER": {
        "env": "FORCE_GET_MAPPER",
        "arg": "--force-get-mapper",
        "type": bool,
        "default": False,
        "help": "Re-generate the mapping file even if it already exists.",
        "section": "Mapping",
        "depends_on": ["SHOULD_GET_MAPPER"]
    },
    "DUMPER7_OUTPUT_DIR": {
        "env": "DUMPER7_OUTPUT_DIR",
        "arg": "--dumper7-output-dir",
        "type": Path,
        "default": None,
        "help": "Path to the where Dumper7 outputs its generated SDK.",
        "help_extended": "If unsure where this is, it is likely `C:/Dumper-7`. Confirm by running the mapper, letting it fail, and checking for the dir.",
        "section": "Mapping",
        "depends_on": ["SHOULD_GET_MAPPER"],
        "example": Path("C:/Dumper-7")
    },
    "OUTPUT_MAPPER_FILE": {
        "env": "OUTPUT_MAPPER_FILE",
        "arg": "--output-mapper-file",
        "type": Path,
        "default": None,
        "help": "Path to save the generated mapping file (.usmap) at. Should end in .usmap",
        "section": "Mapping",
        "depends_on": ["SHOULD_GET_MAPPER", "SHOULD_BATCH_EXPORT"],
        "example": Path("C:/WRFrontiersDB/Mappings/2025-09-30.usmap")
    },
    "SHOULD_BATCH_EXPORT": {
        "env": "SHOULD_BATCH_EXPORT",
        "arg": "--should-batch-export",
        "type": bool,
        "default": False,
        "help": "Whether to run the BatchExport tool to export assets.",
        "section": "Batch Export",
    },
    "FORCE_EXPORT": {
        "env": "FORCE_EXPORT",
        "arg": "--force-export",
        "type": bool,
        "default": False,
        "help": "Re-run the BatchExport even if output directory is not empty.",
        "section": "Batch Export",
        "depends_on": ["SHOULD_BATCH_EXPORT"]
    },
    "OUTPUT_DATA_DIR": {
        "env": "OUTPUT_DATA_DIR",
        "arg": "--output-data-dir",
        "type": Path,
        "default": None,
        "help": "Path to save the exported assets to.",
        "section": "Batch Export",
        "depends_on": ["SHOULD_BATCH_EXPORT"],
        "example": Path("C:/WRFrontiersDB/ExportedData")
    },
    "SHOULD_EXPORT_TEXTURES": {
        "env": "SHOULD_EXPORT_TEXTURES",
        "arg": "--should-export-textures",
        "type": bool,
        "default": True,
        "help": "Whether to export textures.",
        "section": "Batch Export",
        "depends_on": ["SHOULD_BATCH_EXPORT"]
    }
}