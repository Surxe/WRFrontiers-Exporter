# Add two levels of parent dirs to sys path
import sys
import os
import time
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import init_params, Params, clear_dir, wait_for_process_ready_for_injection, terminate_process_by_name, terminate_process_object, is_admin
from mapper.simple_injector import inject_dll_into_process
from loguru import logger
import subprocess

def get_dll_path():
    dll_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mapper', 'Dumper-7.dll')
    if not os.path.exists(dll_path):
        raise Exception(f"DLL file not found: {dll_path}")
    logger.info(f"DLL file confirmed: {dll_path}")
    return dll_path


def get_mapping_file_path(params=None):
    """
    Get the path to the mapping file by running the complete mapper process.
    The returned path will be the final output location (params.output_mapper_file) 
    if copying is successful, otherwise the original extracted location.
    
    Args:
        params (Params, optional): Parameters object. If None, will initialize from default params.
        
    Returns:
        str: Path to the mapping file (preferably at the output location)
    """
    if params is None:
        from utils import init_params
        params = init_params()
    
    return main(params)


def find_existing_mapping_file(dumper7_output_dir):
    """
    Check if a mapping file already exists in the Dumper-7 output directory.
    
    Args:
        dumper7_output_dir (str): Path to the Dumper-7 output directory
        
    Returns:
        str or None: Path to the mapping file if found, None otherwise
    """
    try:
        return get_mapper_from_sdk(dumper7_output_dir)
    except Exception:
        return None


def copy_mapper_file_to_output(source_mapper_path, output_mapper_file):
    """
    Copy a mapper file from source to output location.
    
    Args:
        source_mapper_path (str): Path to the source mapper file
        output_mapper_file (str): Full file path where the mapper file should be copied (including filename)
        
    Returns:
        str: Path to the copied file if successful, None otherwise
    """
    try:
        if not os.path.exists(source_mapper_path):
            logger.error(f"Source mapper file does not exist: {source_mapper_path}")
            return None
        
        # Ensure the parent directory exists
        parent_dir = os.path.dirname(output_mapper_file)
        os.makedirs(parent_dir, exist_ok=True)
        
        # Copy the mapper file
        shutil.copy2(source_mapper_path, output_mapper_file)
        logger.info(f"Mapper file copied from {source_mapper_path} to {output_mapper_file}")
        
        return output_mapper_file
        
    except Exception as e:
        logger.error(f"Failed to copy mapper file: {e}")
        return None


def get_mapper_from_sdk(dumper7_output_dir):
    """
    Extract the mapper file path from the Dumper-7 SDK output directory.
    
    Args:
        dumper7_output_dir (str): Path to the Dumper-7 output directory
        
    Returns:
        str: Path to the mapper file
        
    Raises:
        Exception: If SDK directory structure is invalid or mapper file not found
    """
    # If more than 1 dir (name does not matter) exists in the Dumper-7 output path, throw an error
    sdk_dirs = [d for d in os.listdir(dumper7_output_dir) if os.path.isdir(os.path.join(dumper7_output_dir, d))]
    if len(sdk_dirs) != 1:
        logger.error(f"Expected exactly one directory in Dumper-7 output path, found {len(sdk_dirs)}: {sdk_dirs}")
        raise Exception(f"Invalid SDK directory structure: found {len(sdk_dirs)} directories instead of 1")
    
    # If exactly one dir, check if the Mappings dir exists within it
    mapper_dir = os.path.join(dumper7_output_dir, sdk_dirs[0], 'Mappings')
    if not os.path.exists(mapper_dir):
        logger.error(f"Mappings directory not found in Dumper-7 output: {mapper_dir}")
        raise Exception(f"Mappings directory not found: {mapper_dir}")
    
    logger.info(f"SDK creation appears to have succeeded - found Mappings directory: {mapper_dir}")
    
    # If mappings dir exists, get the file names
    mapper_files = [f for f in os.listdir(mapper_dir) if os.path.isfile(os.path.join(mapper_dir, f))]
    if len(mapper_files) == 0:
        logger.error(f"No mapper files found in Mappings directory: {mapper_dir}")
        raise Exception(f"No mapper files found in: {mapper_dir}")
    elif len(mapper_files) > 1:
        logger.error(f"Multiple mapper files found in Mappings directory, expected only one: {mapper_files}")
        raise Exception(f"Multiple mapper files found, expected only one: {mapper_files}")
    
    mapper_file_path = os.path.join(mapper_dir, mapper_files[0])

    if not os.path.exists(mapper_file_path):
        logger.error(f"Mapper file not found at expected location: {mapper_file_path}")
        raise Exception(f"Mapper file not found: {mapper_file_path}")

    logger.info(f"Mapper file successfully created: {mapper_file_path}")
    return mapper_file_path


def launch_game_process(shipping_cmd_path):
    """
    Launch the game process.
    
    Args:
        shipping_cmd_path (str): Path to the game executable
        
    Returns:
        subprocess.Popen: The game process object
    """
    launch_game_params = [shipping_cmd_path]
    
    # Use subprocess.Popen directly to start game with normal window behavior
    game_process = subprocess.Popen(launch_game_params)
    logger.info(f"Game process started with PID: {game_process.pid}")
    
    # Check if the process started successfully
    time.sleep(2)  # Give it a moment to start
    if game_process.poll() is not None:
        raise Exception(f"Game process failed to start (exit code: {game_process.returncode})")
    
    return game_process


def terminate_game_process(game_process, game_process_name):
    """
    Terminate the game process.
    
    Args:
        game_process (subprocess.Popen): The game process object
        game_process_name (str): Name of the game process
    """
    wait = 10
    logger.info(f"Waiting {wait} seconds before terminating game process just in case the dll did inject and just needs time to process...")
    time.sleep(wait)

    # Always try to terminate the game when done
    logger.info("Terminating game process...")
    
    # First try terminating the subprocess object
    if not terminate_process_object(game_process, 'launch-game'):
        # If that fails, try terminating by process name
        terminate_process_by_name(game_process_name)


def perform_dll_injection(game_process_name, dll_path):
    """
    Perform DLL injection into the game process.
    
    Args:
        game_process_name (str): Name of the game process
        dll_path (str): Path to the DLL file
        
    Returns:
        bool: True if injection was successful, False otherwise
    """
    # Wait for the game to be ready for injection
    logger.info("Waiting for game to be ready for DLL injection...")
    wait_for_process_ready_for_injection(game_process_name, initialization_time=10)
    
    logger.info("Game is ready, starting SDK creation process via DLL injection...")
    
    # Use Python-based DLL injection instead of external injector
    injection_success = inject_dll_into_process(game_process_name, dll_path)
    
    if injection_success:
        logger.info("SDK creation process completed successfully!")
    
    return injection_success


def main(params=None):
    if params is None:
        raise ValueError("Params must be provided")

    game_process_name = os.path.basename(params.shipping_cmd_path)

    logger.info(f"Clearing Dumper-7 output directory: {params.dumper7_output_dir}")
    clear_dir(params.dumper7_output_dir)  # Clear Dumper-7 output directory before starting the game to ensure only new dumps are present

    # Launch the game normally (with window/UI) but don't wait for it to complete
    logger.info("Starting game process with UI...")

    # Check if running as administrator (required for DLL injection)
    if not is_admin():
        logger.warning("Not running as administrator - DLL injection will likely fail. Launch IDE or script as administrator.")
    else:
        logger.info("Running with administrator privileges")

    # Verify DLL file exists before bothering launching the game
    dll_path = get_dll_path()
    
    # Launch the game process
    game_process = launch_game_process(params.shipping_cmd_path)
    has_terminated = False
    mapping_file_path = None
    
    try:
        # Perform DLL injection
        injection_success = perform_dll_injection(game_process_name, dll_path)
        
        if not injection_success:
            raise Exception("DLL injection failed")

    # If it says it errors, it may have actually worked. This actually happens every time for me so long as I'm running as administrator, but I don't know why.
    except Exception as e:
        terminate_game_process(game_process, game_process_name)
        has_terminated = True

        logger.warning("DLL injection says it failed, but it could be incorrect. Checking if the mapping file was created...")
        mapping_file_path = get_mapper_from_sdk(params.dumper7_output_dir)
        if mapping_file_path is None:
            logger.error("DLL injection failed and mapping file was not created. Cannot continue.")
            raise e
        
    if not has_terminated:
        terminate_game_process(game_process, game_process_name)

    if mapping_file_path is None:
        # If we didn't already get the mapper file path from the exception handler, try to get it now 
        mapping_file_path = get_mapper_from_sdk(params.dumper7_output_dir)

    # Copy the mapper file to the output path with the desired filename
    if not mapping_file_path:
        raise Exception("Mapper file path could not be determined after SDK creation")
    
    # Ensure the parent directory exists
    parent_dir = os.path.dirname(params.output_mapper_file)
    os.makedirs(parent_dir, exist_ok=True)
    
    # Copy the mapper file to the specified path and filename
    # This will use the filename from params.output_mapper_file, not the original extracted filename
    shutil.copy2(mapping_file_path, params.output_mapper_file)
    logger.info(f"Mapper file copied from {mapping_file_path} to {params.output_mapper_file}")


if __name__ == '__main__':
    Params()
    params = init_params()
    main(params)