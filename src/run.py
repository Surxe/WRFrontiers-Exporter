#!/usr/bin/env python3
"""
WRFrontiers-Exporter Main Runner

This script orchestrates the complete WRFrontiers data extraction process:
1. Dependency Manager - Downloads/updates all required dependencies
2. Steam Download/Update - Downloads/updates game files via DepotDownloader
3. DLL Injection for Mapper - Creates mapper file via game injection
4. BatchExport - Converts game assets to JSON format

Usage:
    python run.py [options]

Example:
    python run.py --help
"""

import sys
import os
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from params import init_params, ArgumentWriter
from loguru import logger
import traceback
from dependency_manager import main as dependency_main


def run_dependency_manager(params):
    """
    Run the dependency manager to download/update all required dependencies.
    
    Args:
        params (Params): Configuration parameters
        
    Returns:
        bool: True if successful, False otherwise
    """
    start_time = time.time()
    logger.debug(f"Dependency manager timer started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    try:
        logger.info("=" * 60)
        logger.info("STEP 1: DEPENDENCY MANAGER")
        logger.info("=" * 60)
        
        logger.info("Running dependency manager to ensure all dependencies are up to date...")
        result = dependency_main(force_download=params.force_download_dependencies)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Dependency manager timer ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"Dependency manager execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        logger.success("Dependency manager completed successfully!")
        return True
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Dependency manager timer ended (with error) at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"Dependency manager execution time before error: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        logger.error(f"Dependency manager failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def run_steam_download_update(params):
    """
    Run DepotDownloader to download/update the latest War Robots Frontiers game version.
    
    Args:
        params (Params): Configuration parameters
        
    Returns:
        bool: True if successful, False otherwise
    """
    start_time = time.time()
    logger.debug(f"Steam download/update timer started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    try:
        logger.info("=" * 60)
        logger.info("STEP 2: STEAM DOWNLOAD/UPDATE")
        logger.info("=" * 60)
        
        from steam.run_depot_downloader import DepotDownloader
        
        logger.info("Running DepotDownloader to download/update War Robots Frontiers...")
        logger.info(f"Target download path: {params.steam_game_download_path}")
        
        downloader = DepotDownloader(
            wrf_dir=params.steam_game_download_path,
            steam_username=params.steam_username,
            steam_password=params.steam_password,
            force=params.force_steam_download,
        )
        result = downloader.run(manifest_id=params.manifest_id)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Steam download/update timer ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"Steam download/update execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        logger.success("Steam download/update completed successfully!")
        return True
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Steam download/update timer ended (with error) at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"Steam download/update execution time before error: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        logger.error(f"Steam download/update failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def run_mapper_creation(params):
    """
    Run DLL injection process to create the mapper file.
    
    Args:
        params (Params): Configuration parameters
        
    Returns:
        str or None: Path to the created mapper file if successful, None otherwise
    """
    start_time = time.time()
    logger.debug(f"Mapper creation timer started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    try:
        logger.info("=" * 60)
        logger.info("STEP 3: DLL INJECTION FOR MAPPER FILE")
        logger.info("=" * 60)
        
        from mapper.get_mapper import main as mapper_main
        
        logger.info("Running DLL injection to create mapper file...")
        logger.info(f"Steam game download path: {params.steam_game_download_path}")
        logger.info(f"Dumper-7 output directory: {params.dumper7_output_dir}")
        logger.info(f"Output mapper file: {params.output_mapper_file}")
        
        mapper_file_path = mapper_main(params)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Mapper creation timer ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"Mapper creation execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        if mapper_file_path and os.path.exists(mapper_file_path):
            logger.success(f"Mapper file created successfully: {mapper_file_path}")
            return mapper_file_path
        else:
            logger.error("Mapper file creation failed - file does not exist")
            return None
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Mapper creation timer ended (with error) at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"Mapper creation execution time before error: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        logger.error(f"Mapper creation failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def run_batch_export(params, mapper_file_path):
    """
    Run BatchExport to convert game assets to JSON format.
    
    Args:
        params (Params): Configuration parameters
        mapper_file_path (str): Path to the mapper file
        
    Returns:
        bool: True if successful, False otherwise
    """
    start_time = time.time()
    logger.debug(f"BatchExport timer started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    try:
        logger.info("=" * 60)
        logger.info("STEP 4: BATCHEXPORT")
        logger.info("=" * 60)
        
        # Import with correct module name (handle hyphen in directory name)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_batch_export", 
            os.path.join(os.path.dirname(__file__), "cue4p-batchexport", "run_batch_export.py")
        )
        run_batch_export_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_batch_export_module)
        batchexport_main = run_batch_export_module.main
        
        logger.info("Running BatchExport to convert game assets to JSON...")
        logger.info(f"Using mapper file: {mapper_file_path}")
        logger.info(f"Source PAK files: {params.steam_game_download_path}")
        logger.info(f"Output JSON directory: {params.output_data_dir}")
        
        result = batchexport_main(params, mapper_file_path)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"BatchExport timer ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"BatchExport execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        if result:
            logger.success("BatchExport completed successfully!")
            return True
        else:
            logger.error("BatchExport failed")
            return False
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"BatchExport timer ended (with error) at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.debug(f"BatchExport execution time before error: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        logger.error(f"BatchExport failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def validate_environment(params):
    """
    Validate that all required environment variables and paths are properly configured.
    
    Args:
        params (Params): Configuration parameters
        
    Returns:
        bool: True if environment is valid, False otherwise
    """
    try:
        logger.info("Validating environment configuration...")
        
        # This will raise an exception if any required parameters are missing
        params.validate()
        
        logger.success("Environment validation passed!")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False


def main(args):
    """
    Main function to run the complete WRFrontiers-Exporter process.
        
    Returns:
        bool: True if all steps completed successfully, False otherwise
    """
    overall_start_time = time.time()
    logger.debug(f"WRFrontiers-Exporter overall timer started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(overall_start_time))}")
    
    try:
        logger.info("Starting WRFrontiers-Exporter Complete Process")
        logger.info("=" * 80)
        
        # Initialize parameters with provided arguments
        params = init_params(args)
        
        # Validate environment
        if not validate_environment(params):
            logger.error("Environment validation failed. Cannot continue.")
            return False
        
        # Step 1: Dependency Manager
        if params.should_download_dependencies:
            if not run_dependency_manager(params):
                logger.error("Dependency manager failed. Cannot continue.")
                return False
        else:
            logger.info("Skipping dependency manager step...")
        
        # Step 2: Steam Download/Update
        if params.should_download_steam_game:
            if not run_steam_download_update(params):
                logger.error("Steam download/update failed. Cannot continue.")
                return False
        else:
            logger.info("Skipping steam download/update step...")
        
        # Step 3: Mapper Creation
        mapper_file_path = None
        if params.should_get_mapper:
            mapper_file_path = run_mapper_creation(params)
            if not mapper_file_path:
                logger.error("Mapper creation failed. Cannot continue.")
                return False
        else:
            logger.info("Skipping mapper creation step...")
        
        # Step 4: BatchExport
        if params.should_batch_export:
            # If skipped mapper creation, use the expected output path
            mapper_file_path = params.output_mapper_file
            if not os.path.exists(mapper_file_path):
                logger.error(f"Mapper file not found at {mapper_file_path}. Cannot skip mapper creation.")
                return False
            if not run_batch_export(params, mapper_file_path):
                logger.error("BatchExport failed.")
                return False
        else:
            logger.info("Skipping batch export step...")
        
        # Success!
        overall_end_time = time.time()
        overall_elapsed_time = overall_end_time - overall_start_time
        logger.debug(f"WRFrontiers-Exporter overall timer ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(overall_end_time))}")
        logger.debug(f"Total WRFrontiers-Exporter execution time: {overall_elapsed_time:.2f} seconds ({overall_elapsed_time/60:.2f} minutes)")
        
        logger.info("=" * 80)
        logger.success("WRFrontiers-Exporter Complete Process Finished Successfully!")
        logger.info("=" * 80)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user (Ctrl+C)")
        return False
    except Exception as e:
        overall_end_time = time.time()
        overall_elapsed_time = overall_end_time - overall_start_time
        logger.debug(f"WRFrontiers-Exporter overall timer ended (with error) at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(overall_end_time))}")
        logger.debug(f"Total WRFrontiers-Exporter execution time before error: {overall_elapsed_time:.2f} seconds ({overall_elapsed_time/60:.2f} minutes)")
        
        logger.error(f"Unexpected error in main process: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="WRFrontiers-Exporter - Complete game data extraction pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
For detailed documentation including all command line arguments, configuration options,
and troubleshooting information, please see the README.md file.

Quick Examples:
  python run.py                              # Run all steps with default values
  python run.py --skip-dependencies         # Skip dependency check/update
  python run.py --log-level INFO            # Set log level to INFO
        """
    )
    
    argument_writer = ArgumentWriter()
    argument_writer.add_arguments(parser)
    
    args = parser.parse_args()
    
    # Run the main process with parsed arguments
    success = main(args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
