# Add two levels of parent dirs to sys path
import sys
import os
import time
import platform
from pathlib import Path
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optionsconfig import init_options, Options
from utils import run_process, executable_name
from loguru import logger

class BatchExporter:
    """
    A class to handle batch exporting of game assets using the CUE4P BatchExport tool.
    
    This class manages the execution of BatchExport.exe with the appropriate options
    for extracting War Robots Frontiers game data from .pak files to JSON format.
    """
    
    def __init__(self, options: Optional[Options] = None, mapping_file_path: Optional[str] = None) -> None:
        """
        Initialize the BatchExporter.
        
        Args:
            options (Options, optional): Options object containing configuration. If None, will create default.
            mapping_file_path (str): Path to the mapping file for UE4 assets (required)
        """
        if options is None:
            options = init_options()
        
        if mapping_file_path is None:
            raise ValueError("mapping_file_path is required for BatchExporter")
        
        self.options = options
        self.mapping_file_path = mapping_file_path
        
        # Path to BatchExport executable (platform-aware: .exe on Windows, bare on Linux)
        self.batch_export_dir = Path(__file__).parent / "BatchExport"
        self.executable_path = self.batch_export_dir / executable_name("BatchExport")
        
        # Build the command once during initialization
        self.command = [
            str(self.executable_path),
            "--preset", "WarRobotsFrontiers",
            "--pak-files-directory", str(self.options.steam_game_download_dir),
            "--export-output-path", str(self.options.output_data_dir),
            "--mapping-file-path", str(self.mapping_file_path),
            "--is-logging-enabled", "true" if self.options.log_level == "DEBUG" else "false",
            "--should-export-textures", "false" if not self.options.should_export_textures else "true"
        ]
        
        # Validate paths
        self._validate_setup()
    
    def _validate_setup(self) -> None:
        """Validate that all required paths and files exist."""
        if not self.executable_path.exists():
            raise FileNotFoundError(
                f"BatchExport.exe not found at {self.executable_path}. "
                "Please use should_download_dependencies first to download it."
            )
        
        if not os.path.exists(self.options.steam_game_download_dir):
            raise FileNotFoundError(
                f"Steam game download path not found: {self.options.steam_game_download_dir}. "
                "Please ensure steam_game_download_dir is set correctly in your environment."
            )
        
        # Create output data directory if it doesn't exist
        os.makedirs(self.options.output_data_dir, exist_ok=True)
        logger.info(f"Ensured output data directory exists: {self.options.output_data_dir}")
        
        # Ensure its parent dir exists, but not the file
        parent_dir = os.path.dirname(self.mapping_file_path)
        if not os.path.exists(parent_dir):
            raise FileNotFoundError(
                f"Parent directory for mapping file not found: {parent_dir}. "
                "Please ensure the directory exists."
            )
    
    def run(self) -> None:
        """
        Execute BatchExport with the configured options.
        
        Returns:
            None: The process completes successfully or raises an exception
            
        Raises:
            RuntimeError: If BatchExport execution fails
        """
        logger.info("Starting BatchExport process...")
        logger.info(f"Using mapping file: {self.mapping_file_path}")
        logger.info(f"Executing BatchExport with command: {str(self)}")
        logger.info(f"PAK files directory: {self.options.steam_game_download_dir}")
        logger.info(f"Export output path: {self.options.output_data_dir}")
        
        try:
            # On Linux the native decompression libs (Oodle, Detex) live next to
            # the BatchExport binary and are loaded by bare name via dlopen, which
            # only searches LD_LIBRARY_PATH + system dirs (not the app dir). Add
            # the binary's directory to LD_LIBRARY_PATH so they resolve.
            proc_env = None
            if platform.system().lower() == 'linux':
                proc_env = os.environ.copy()
                existing = proc_env.get('LD_LIBRARY_PATH', '')
                proc_env['LD_LIBRARY_PATH'] = (
                    f"{self.batch_export_dir}:{existing}" if existing else str(self.batch_export_dir)
                )

            # Execute BatchExport using run_process from utils
            # run_process handles logging, timeouts, and error handling internally
            run_process(
                options=self.command,
                name="BatchExport",
                timeout=3600,  # 1 hour timeout
                env=proc_env
            )
            
            logger.success("BatchExport completed successfully!")
            
        except Exception as e:
            error_msg = f"BatchExport execution failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def __str__(self) -> str:
        """Return the command that would be executed as a string."""
        return ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in self.command)


def main(options: Optional[Options] = None, mapping_file_path: Optional[str] = None) -> bool:
    """
    Main function to run BatchExport with the given options.
    
    Args:
        options (Options, optional): Configuration options
        mapping_file_path (str): Path to the mapping file (required)
    """
    if options is None:
        raise ValueError("Options must be provided")
    
    if mapping_file_path is None:
        raise ValueError("mapping_file_path must be provided")
    
    # Check if export directory has contents and force is False
    if os.path.exists(options.output_data_dir) and os.listdir(options.output_data_dir) and not options.force_export:
        logger.info(f"Export directory {options.output_data_dir} already has contents and FORCE_EXPORT is False. Skipping batch export.")
        return True
    
    try:
        batch_exporter = BatchExporter(options, mapping_file_path)
        
        # Show command preview
        logger.info(f"Command to execute: {str(batch_exporter)}")
        
        # Run BatchExport
        batch_exporter.run()
        
        logger.success("BatchExport process completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"BatchExport failed: {e}")
        raise