from dotenv import load_dotenv

import os
import sys
import os
from typing import Literal
from pathlib import Path
from loguru import logger
load_dotenv()

from utils import is_truthy

"""
Central configuration schema to provide a single source of truth for all documentation and functionality of params/args
"""

PARAMETER_SCHEMA = {
    "LOG_LEVEL": {
        "env": "LOG_LEVEL",
        "arg": "--log-level",
        "type": Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "default": "DEBUG",
        "section": "Logging",
        "help": "Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL. Default: 'DEBUG'."
    },
    "SHOULD_DOWNLOAD_DEPENDENCIES": {
        "env": "SHOULD_DOWNLOAD_DEPENDENCIES",
        "arg": "--download-dependencies",
        "type": bool,
        "default": True,
        "help": "Whether to download dependencies.",
        "section": "Dependencies",
        "section_params": {
            "FORCE_DOWNLOAD_DEPENDENCIES": {
                "env": "FORCE_DOWNLOAD_DEPENDENCIES",
                "arg": "--force-download-dependencies",
                "type": bool,
                "default": False,
                "section": "Dependencies",
                "section_reliant_param": "SHOULD_DOWNLOAD_DEPENDENCIES",
                "help": "Re-download dependencies even if they are already present. Default: False."
            }
        }
    },
    "SHOULD_DOWNLOAD_STEAM_GAME": {
        "env": "SHOULD_DOWNLOAD_STEAM_GAME",
        "arg": "--download-steam-game",
        "type": bool,
        "default": True,
        "help": "Whether to download Steam game files. Default: True.",
        "section": "Steam Download",
        "section_params": {
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
        "arg": "--get-mapper",
        "type": bool,
        "default": True,
        "help": "Whether to get the mapping file using Dumper7.",
        "section": "Mapping",
        "section_params": {
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
                "help_extended": "If unsure where this is, it is likely C:/Dumper-7. Confirm by running the mapper, letting it fail, and checking for the dir."
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
    "SHOULD_RUN_BATCH_EXPORT": {
        "env": "SHOULD_RUN_BATCH_EXPORT",
        "arg": "--run-batch-export",
        "type": bool,
        "default": True,
        "help": "Whether to run the BatchExport tool to export assets.",
        "section": "Batch Export",
        "section_params": {
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

class Params:
    """
    A class to hold parameters for the application.
    """
    def __init__(self, log_level=None, force_download_dependencies=None,
                 manifest_id=None, force_steam_download=None, steam_username=None, steam_password=None, steam_game_download_path=None,
                 dumper7_output_dir=None, 
                 output_mapper_file=None, force_get_mapper=None, output_data_dir=None, force_export=None,
                 skip_dependencies=None, skip_steam_update=None, skip_mapper=None, skip_batch_export=None):
        
        # Use provided args if not None, else fallback to environment
        self.log_level = (log_level if log_level is not None else os.getenv('LOG_LEVEL', 'DEBUG')).upper()
        
        # Dependencies
        self.force_download_dependencies = is_truthy(force_download_dependencies if force_download_dependencies is not None else (os.getenv('FORCE_DOWNLOAD_DEPENDENCIES', 'False').lower() == 'true'))
        
        # Steam download
        self.manifest_id = manifest_id if manifest_id is not None else os.getenv('MANIFEST_ID')
        self.manifest_id = self.manifest_id if self.manifest_id != "" else None  # Treat empty string as None
        self.force_steam_download = is_truthy(force_steam_download if force_steam_download is not None else (os.getenv('FORCE_STEAM_DOWNLOAD', 'False').lower() == 'true'))
        self.steam_username = steam_username if steam_username is not None else os.getenv('STEAM_USERNAME')
        self.steam_password = steam_password if steam_password is not None else os.getenv('STEAM_PASSWORD')
        self.steam_game_download_path = steam_game_download_path if steam_game_download_path is not None else os.getenv('STEAM_GAME_DOWNLOAD_PATH')
        
        # Mapping
        self.dumper7_output_dir = dumper7_output_dir if dumper7_output_dir is not None else os.getenv('DUMPER7_OUTPUT_DIR')
        self.output_mapper_file = output_mapper_file if output_mapper_file is not None else os.getenv('OUTPUT_MAPPER_FILE')
        self.force_get_mapper = is_truthy(force_get_mapper if force_get_mapper is not None else (os.getenv('FORCE_GET_MAPPER', 'True').lower() == 'true'))
        
        # BatchExport
        self.output_data_dir = output_data_dir if output_data_dir is not None else os.getenv('OUTPUT_DATA_DIR')
        self.force_export = is_truthy(force_export if force_export is not None else (os.getenv('FORCE_EXPORT', 'True').lower() == 'true'))
        
        # Skip options
        self.skip_dependencies = is_truthy(skip_dependencies if skip_dependencies is not None else (os.getenv('SKIP_DEPENDENCIES', 'False').lower() == 'true'))
        self.skip_steam_update = is_truthy(skip_steam_update if skip_steam_update is not None else (os.getenv('SKIP_STEAM_UPDATE', 'False').lower() == 'true'))
        self.skip_mapper = is_truthy(skip_mapper if skip_mapper is not None else (os.getenv('SKIP_MAPPER', 'False').lower() == 'true'))
        self.skip_batch_export = is_truthy(skip_batch_export if skip_batch_export is not None else (os.getenv('SKIP_BATCH_EXPORT', 'False').lower() == 'true'))
        
        # Setup loguru logging to /logs dir
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        if self.output_data_dir:
            log_filename = self.output_data_dir.replace('\\', '/').rstrip('/').split('/')[-1] + '.log'
            # i.e. F:/WRF/2025-08-12/<exports> to 2025-08-12.log
        else:
            log_filename = 'default.log'
        log_path = os.path.join(logs_dir, log_filename)
        logger.remove()
        
        # Clear the log file before adding the handler
        with open(log_path, 'w') as f:
            pass
        logger.add(log_path, level=self.log_level, rotation="10 MB", retention="10 days", enqueue=True)
        logger.add(sys.stdout, level=self.log_level)
        
        self.validate()
        self.log()

    def validate(self):
        """
        Validates the parameters.
        """
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"LOG_LEVEL {self.log_level} must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.")

        # Dependencies
        if not isinstance(self.force_download_dependencies, bool):
            raise ValueError("FORCE_DOWNLOAD_DEPENDENCIES must be a boolean value (True or False).")

        # Steam download
        if not isinstance(self.force_steam_download, bool):
            raise ValueError("FORCE_STEAM_DOWNLOAD must be a boolean value (True or False).")

        if not self.steam_username:
            raise ValueError("STEAM_USERNAME environment variable is not set.")

        if not self.steam_password:
            raise ValueError("STEAM_PASSWORD environment variable is not set.")
        
        if not self.steam_game_download_path:
            raise ValueError("STEAM_GAME_DOWNLOAD_PATH environment variable is not set.")
        if not os.path.exists(self.steam_game_download_path):
            raise ValueError(f"STEAM_GAME_DOWNLOAD_PATH '{self.steam_game_download_path}' does not exist.")
        

        # Mapping
        if not self.dumper7_output_dir:
            raise ValueError("DUMPER7_OUTPUT_DIR environment variable is not set.")
        if not os.path.exists(self.dumper7_output_dir):
            raise ValueError(f"DUMPER7_OUTPUT_DIR '{self.dumper7_output_dir}' does not exist.")
        if not self.output_mapper_file:
            raise ValueError("OUTPUT_MAPPER_FILE environment variable is not set.")
        # Just check that its parent dir exists, the file itself will be created
        parent_dir = os.path.dirname(self.output_mapper_file)
        if not os.path.exists(parent_dir):
            raise ValueError(f"Parent directory for OUTPUT_MAPPER_FILE '{self.output_mapper_file}' does not exist.")
        if not isinstance(self.force_get_mapper, bool):
            raise ValueError("FORCE_GET_MAPPER must be a boolean value (True or False).")

        # BatchExport
        if not self.output_data_dir:
            raise ValueError("OUTPUT_DATA_DIR environment variable is not set.")
        
        # Validate parent directories exist for output_data_dir
        parent_dir = os.path.dirname(self.output_data_dir)
        if parent_dir and not os.path.exists(parent_dir):
            raise ValueError(f"Parent directory for OUTPUT_DATA_DIR does not exist: {parent_dir}")
        
        if not isinstance(self.force_export, bool):
            raise ValueError("FORCE_EXPORT must be a boolean value (True or False).")
        
        # Skip options
        if not isinstance(self.skip_dependencies, bool):
            raise ValueError("SKIP_DEPENDENCIES must be a boolean value (True or False).")
        if not isinstance(self.skip_steam_update, bool):
            raise ValueError("SKIP_STEAM_UPDATE must be a boolean value (True or False).")
        if not isinstance(self.skip_mapper, bool):
            raise ValueError("SKIP_MAPPER must be a boolean value (True or False).")
        if not isinstance(self.skip_batch_export, bool):
            raise ValueError("SKIP_BATCH_EXPORT must be a boolean value (True or False).")
        
        # Log parameters after all validation
        logger.debug(f"Force download dependencies: {self.force_download_dependencies}")
        
    def log(self):
        """
        Logs the parameters.
        """
        logger.info(
            f"Params initialized with:\n"
            f"LOG_LEVEL: {self.log_level}\n"
            
            f"MANIFEST_ID: {self.manifest_id}\n"
            f"FORCE_STEAM_DOWNLOAD: {self.force_steam_download}\n"
            f"STEAM_USERNAME: {self.steam_username}\n"
            #f"STEAM_PASSWORD: {self.steam_password}\n"
            f"STEAM_GAME_DOWNLOAD_PATH: {self.steam_game_download_path}\n"
            
            f"DUMPER7_OUTPUT_DIR: {self.dumper7_output_dir}\n"
            f"OUTPUT_MAPPER_FILE: {self.output_mapper_file}\n"
            f"FORCE_GET_MAPPER: {self.force_get_mapper}\n"

            f"OUTPUT_DATA_DIR: {self.output_data_dir}\n"
            f"FORCE_EXPORT: {self.force_export}\n"
            
            f"SKIP_DEPENDENCIES: {self.skip_dependencies}\n"
            f"SKIP_STEAM_UPDATE: {self.skip_steam_update}\n"
            f"SKIP_MAPPER: {self.skip_mapper}\n"
            f"SKIP_BATCH_EXPORT: {self.skip_batch_export}\n"
        )

    def __str__(self):
        return f"Params(export_path={self.export_path}, game_name={self.game_name}, log_level={self.log_level})"
    
# Helper to initialize PARAMS with direct args if available
def init_params(log_level=None, force_download_dependencies=None, manifest_id=None, force_steam_download=None, 
                steam_username=None, steam_password=None, steam_game_download_path=None, dumper7_output_dir=None,
                output_mapper_file=None, force_get_mapper=None, output_data_dir=None, force_export=None,
                skip_dependencies=None, skip_steam_update=None, skip_mapper=None, skip_batch_export=None):
    global PARAMS
    PARAMS = Params(log_level=log_level, force_download_dependencies=force_download_dependencies, manifest_id=manifest_id,
                   force_steam_download=force_steam_download, steam_username=steam_username, steam_password=steam_password,
                   steam_game_download_path=steam_game_download_path, dumper7_output_dir=dumper7_output_dir,
                   output_mapper_file=output_mapper_file, force_get_mapper=force_get_mapper, 
                   output_data_dir=output_data_dir, force_export=force_export,
                   skip_dependencies=skip_dependencies, skip_steam_update=skip_steam_update,
                   skip_mapper=skip_mapper, skip_batch_export=skip_batch_export)
    return PARAMS