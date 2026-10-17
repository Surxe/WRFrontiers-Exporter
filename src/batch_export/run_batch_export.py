# Add two levels of parent dirs to sys path
import sys
import os
import time
import platform
from pathlib import Path
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import shutil

from optionsconfig import init_options, Options
from utils import run_process, executable_name, ProcessExitError
from dependency_manager import BATCH_EXPORT_DIR, BATCH_EXPORT_REPO
from loguru import logger

# WRFrontiersDB-CUE4Parse exit codes (see its README).
EXIT_FAILURES = 1
EXIT_OUT_OF_MEMORY = 3
# A process the kernel killed with SIGKILL: Python reports -9, a shell 137. Under a memory cap
# this is the cgroup OOM killer, when native memory runs out before the GC heap limit.
EXIT_KILLED = (-9, 137)

_SIZE_UNITS = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}


def parse_memory_size(value: str) -> int:
    """Bytes in a systemd-style size such as '1536M', '2G' or '805306368'."""
    match = re.fullmatch(r"\s*(\d+)\s*([KMGT]?)\s*", str(value), re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid memory size: {value!r} (expected e.g. 1536M or 2G)")
    return int(match.group(1)) * _SIZE_UNITS[match.group(2).upper()]


class BatchExporter:
    """
    Runs the WRFrontiersDB-CUE4Parse export: assets, meshes, maps and config, in one process.

    The tool sizes its workers from its memory budget, so the only setting is the memory cap
    (BATCH_EXPORT_MEMORY_MAX). Its release is self-contained, so it runs without environment setup.
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
        
        # Platform-aware: .exe on Windows, bare on Linux
        self.batch_export_dir = BATCH_EXPORT_DIR
        self.executable_path = self.batch_export_dir / executable_name(BATCH_EXPORT_REPO)
        self.memory_max = self.options.batch_export_memory_max
        self.memory_max_bytes = parse_memory_size(self.memory_max)

        # Build the command once during initialization. The tool logs progress by default.
        export_command = [
            str(self.executable_path),
            "--pak-files-directory", str(self.options.steam_game_download_dir),
            "--export-output-path", str(self.options.output_data_dir),
            "--mapping-file-path", str(self.mapping_file_path),
        ]
        self.command, self.env = self._apply_memory_cap(export_command)
        
        # Validate paths
        self._validate_setup()
    
    def _apply_memory_cap(self, export_command: list) -> tuple:
        """
        Caps the export's memory at BATCH_EXPORT_MEMORY_MAX. Returns (command, env).

        On Linux with systemd, the export runs in a transient user scope with MemoryMax set and no
        swap; .NET then sets its GC heap limit to 75% of it. Elsewhere the GC heap limit is set
        directly to that 75%, so the tool computes the same budget.
        """
        env = os.environ.copy()
        if platform.system().lower() == 'linux' and shutil.which("systemd-run"):
            # A system service running as a user with linger has a user manager but no
            # XDG_RUNTIME_DIR; systemd-run --user needs it to find the user bus.
            env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
            command = [
                "systemd-run", "--user", "--scope", "--quiet",
                "-p", f"MemoryMax={self.memory_max}", "-p", "MemorySwapMax=0", "--",
            ] + export_command
            return command, env

        env["DOTNET_GCHeapHardLimit"] = hex(self.memory_max_bytes * 3 // 4)
        return export_command, env

    def _validate_setup(self) -> None:
        """Validate that all required paths and files exist."""
        if not self.executable_path.exists():
            raise FileNotFoundError(
                f"{BATCH_EXPORT_REPO} not found at {self.executable_path}. "
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
        logger.info(f"Starting {BATCH_EXPORT_REPO} export...")
        logger.info(f"Using mapping file: {self.mapping_file_path}")
        logger.info(f"Executing with command: {str(self)}")
        logger.info(f"PAK files directory: {self.options.steam_game_download_dir}")
        logger.info(f"Export output path: {self.options.output_data_dir}")
        logger.info(f"Memory cap: {self.memory_max}")

        try:
            # run_process logs the output line by line and raises on a non-zero exit
            run_process(
                options=self.command,
                name=BATCH_EXPORT_REPO,
                timeout=3600,  # 1 hour timeout
                env=self.env
            )
            logger.success(f"{BATCH_EXPORT_REPO} completed successfully!")

        except ProcessExitError as e:
            error_msg = self.describe_exit(e.exit_code)
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"{BATCH_EXPORT_REPO} execution failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def describe_exit(self, exit_code: int) -> str:
        """What a non-zero exit of the export means, for the log and the raised error."""
        if exit_code == EXIT_OUT_OF_MEMORY:
            return (f"{BATCH_EXPORT_REPO} ran out of memory (exit {exit_code}) under the cap "
                    f"{self.memory_max}. Raise BATCH_EXPORT_MEMORY_MAX.")
        if exit_code in EXIT_KILLED:
            return (f"{BATCH_EXPORT_REPO} was killed (exit {exit_code}), most likely by the kernel "
                    f"for exceeding the memory cap {self.memory_max}. Raise BATCH_EXPORT_MEMORY_MAX.")
        if exit_code == EXIT_FAILURES:
            return (f"{BATCH_EXPORT_REPO} finished with export failures (exit {exit_code}). "
                    "Its summary above lists them.")
        return f"{BATCH_EXPORT_REPO} failed with exit code {exit_code}."
    
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
        logger.info(f"Export directory {options.output_data_dir} already has contents and FORCE_EXPORT is False. Skipping the export.")
        return True
    
    try:
        batch_exporter = BatchExporter(options, mapping_file_path)
        
        # Show command preview
        logger.info(f"Command to execute: {str(batch_exporter)}")
        
        # Run BatchExport
        batch_exporter.run()
        
        logger.success(f"{BATCH_EXPORT_REPO} export completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"BatchExport failed: {e}")
        raise