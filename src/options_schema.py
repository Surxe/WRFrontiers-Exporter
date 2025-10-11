from typing import Literal
from pathlib import Path

"""
# Schema
* **env** - Environment variable name (UPPER_CASE)
* **arg** - Command line argument (kebab-case with --)
* **type** - Python type (bool, str, Path, Literal)
* **default** - Default value. None means its required if it's root option is True
* **help** - Description text
* **section** - Logical grouping name
* **section_options** - Nested sub-options
* **sensitive** - Boolean flag for password masking

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
        "section_options": {
            "FORCE_DOWNLOAD_DEPENDENCIES": {
                "env": "FORCE_DOWNLOAD_DEPENDENCIES",
                "arg": "--force-download-dependencies",
                "type": bool,
                "default": False,
                "section": "Dependencies",
                "section_reliant_option": "SHOULD_DOWNLOAD_DEPENDENCIES",
                "help": "Re-download dependencies even if they are already present."
            }
        }
    },
    "SHOULD_DOWNLOAD_STEAM_GAME": {
        "env": "SHOULD_DOWNLOAD_STEAM_GAME",
        "arg": "--should-download-steam-game",
        "type": bool,
        "default": False,
        "help": "Whether to download Steam game files.",
        "section": "Steam Download",
        "section_options": {
            "FORCE_STEAM_DOWNLOAD": {
                "env": "FORCE_STEAM_DOWNLOAD",
                "arg": "--force-steam-download",
                "type": bool,
                "default": False,
                "help": "Re-download/update Steam game files even if they are already present."
            },
            "MANIFEST_ID": {
                "env": "MANIFEST_ID",
                "arg": "--manifest-id",
                "type": str,
                "default": "",
                "help": "Steam manifest ID to download. If blank, the latest manifest ID will be used.",
                "links": {"SteamDB": "https://steamdb.info/app/1491000/depot/1491005/manifests/"}
            },
            "STEAM_USERNAME": {
                "env": "STEAM_USERNAME",
                "arg": "--steam-username",
                "type": str,
                "default": None,
                "help": "Steam username for authentication.",
            },
            "STEAM_PASSWORD": {
                "env": "STEAM_PASSWORD",
                "arg": "--steam-password",
                "type": str,
                "default": None,
                "sensitive": True,
                "help": "Steam password for authentication.",
            },
            "STEAM_GAME_DOWNLOAD_PATH": {
                "env": "STEAM_GAME_DOWNLOAD_PATH",
                "arg": "--steam-game-download-path",
                "type": Path,
                "default": None,
                "help": "Path to the local Steam game installation directory.",
            },
        },
    },
    "SHOULD_GET_MAPPER": {
        "env": "SHOULD_GET_MAPPER",
        "arg": "--should-get-mapper",
        "type": bool,
        "default": False,
        "help": "Whether to get the mapping file using Dumper7.",
        "section": "Mapping",
        "section_options": {
            "FORCE_GET_MAPPER": {
                "env": "FORCE_GET_MAPPER",
                "arg": "--force-get-mapper",
                "type": bool,
                "default": True,
                "help": "Re-generate the mapping file even if it already exists."
            },
            "DUMPER7_OUTPUT_DIR": {
                "env": "DUMPER7_OUTPUT_DIR",
                "arg": "--dumper7-output-dir",
                "type": Path,
                "default": None,
                "help": "Path to the where Dumper7 outputs its generated SDK.",
                "help_extended": "If unsure where this is, it is likely `C:/Dumper-7`. Confirm by running the mapper, letting it fail, and checking for the dir."
            },
            "OUTPUT_MAPPER_FILE": {
                "env": "OUTPUT_MAPPER_FILE",
                "arg": "--output-mapper-file",
                "type": Path,
                "default": None,
                "help": "Path to save the generated mapping file (.usmap) at. Should end in .usmap",
            },
        }
    },
    "SHOULD_BATCH_EXPORT": {
        "env": "SHOULD_BATCH_EXPORT",
        "arg": "--should-batch-export",
        "type": bool,
        "default": False,
        "help": "Whether to run the BatchExport tool to export assets.",
        "section": "Batch Export",
        "section_options": {
            "FORCE_EXPORT": {
                "env": "FORCE_EXPORT",
                "arg": "--force-export",
                "type": bool,
                "default": True,
                "help": "Re-run the BatchExport even if output directory is not empty."
            },
            "OUTPUT_DATA_DIR": {
                "env": "OUTPUT_DATA_DIR",
                "arg": "--output-data-dir",
                "type": Path,
                "default": None,
                "help": "Path to save the exported assets to.",
            },
        }
    },
}