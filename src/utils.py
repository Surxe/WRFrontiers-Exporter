from dotenv import load_dotenv

import os
import sys
import subprocess
import os
from loguru import logger
load_dotenv()

###############################
#           Params            #
###############################

class Params:
    """
    A class to hold parameters for the application.
    """
    def __init__(self, log_level=None, 
                 depot_download_cmd_path=None, force_download=None, steam_username=None, steam_password=None, steam_game_download_path=None, 
                 shipping_cmd_path=None, dumper7_output_dir=None, 
                 output_mapper_path=None, output_data_dir=None):
        
        # Use provided args if not None, else fallback to environment
        self.log_level = (log_level if log_level is not None else os.getenv('LOG_LEVEL', 'DEBUG')).upper()
        
        # Steam download
        self.depot_downloader_cmd_path = depot_download_cmd_path if depot_download_cmd_path is not None else os.getenv('DEPOT_DOWNLOADER_CMD_PATH')
        self.force_download = is_truthy(force_download if force_download is not None else (os.getenv('FORCE_DOWNLOAD', 'False').lower() == 'true'))
        self.steam_username = steam_username if steam_username is not None else os.getenv('STEAM_USERNAME')
        self.steam_password = steam_password if steam_password is not None else os.getenv('STEAM_PASSWORD')
        self.steam_game_download_path = steam_game_download_path if steam_game_download_path is not None else os.getenv('STEAM_GAME_DOWNLOAD_PATH')
        
        # Mapping
        self.shipping_cmd_path = shipping_cmd_path if shipping_cmd_path is not None else os.getenv('SHIPPING_CMD_PATH')
        self.dumper7_output_dir = dumper7_output_dir if dumper7_output_dir is not None else os.getenv('DUMPER7_OUTPUT_DIR')

        # BatchExport
        self.output_mapper_path = output_mapper_path if output_mapper_path is not None else os.getenv('OUTPUT_MAPPER_PATH')
        self.output_data_dir = output_data_dir if output_data_dir is not None else os.getenv('OUTPUT_DATA_DIR')
        
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

        # Steam download
        if not self.depot_downloader_cmd_path:
            raise ValueError("DEPOT_DOWNLOADER_CMD_PATH environment variable is not set.")
        if not os.path.exists(self.depot_downloader_cmd_path):
            raise ValueError(f"DEPOT_DOWNLOADER_CMD_PATH '{self.depot_downloader_cmd_path}' does not exist.")

        if not isinstance(self.force_download, bool):
            raise ValueError("FORCE_DOWNLOAD must be a boolean value (True or False).")

        if not self.steam_username:
            raise ValueError("STEAM_USERNAME environment variable is not set.")

        if not self.steam_password:
            raise ValueError("STEAM_PASSWORD environment variable is not set.")
        
        if not self.steam_game_download_path:
            raise ValueError("STEAM_GAME_DOWNLOAD_PATH environment variable is not set.")
        if not os.path.exists(self.steam_game_download_path):
            raise ValueError(f"STEAM_GAME_DOWNLOAD_PATH '{self.steam_game_download_path}' does not exist.")
        

        # Mapping
        if not self.shipping_cmd_path:
            raise ValueError("SHIPPING_CMD_PATH environment variable is not set.")
        if not os.path.exists(self.shipping_cmd_path):
            raise ValueError(f"SHIPPING_CMD_PATH '{self.shipping_cmd_path}' does not exist.")
        
        if not self.dumper7_output_dir:
            raise ValueError("DUMPER7_OUTPUT_DIR environment variable is not set.")
        if not os.path.exists(self.dumper7_output_dir):
            raise ValueError(f"DUMPER7_OUTPUT_DIR '{self.dumper7_output_dir}' does not exist.")
        

        # BatchExport
        if not self.output_mapper_path:
            raise ValueError("OUTPUT_MAPPER_PATH environment variable is not set.")
        # Just check that its parent dir exists, the file itself will be created
        parent_dir = os.path.dirname(self.output_mapper_path)
        if not os.path.exists(parent_dir):
            raise ValueError(f"Parent directory for OUTPUT_MAPPER_PATH '{self.output_mapper_path}' does not exist.")

        if not self.output_data_dir:
            raise ValueError("OUTPUT_DATA_DIR environment variable is not set.")
        if not os.path.exists(self.output_data_dir):
            raise ValueError(f"OUTPUT_DATA_DIR '{self.output_data_dir}' does not exist.")
        
    def log(self):
        """
        Logs the parameters.
        """
        logger.info(
            f"Params initialized with:\n"
            f"LOG_LEVEL: {self.log_level}\n"
            
            f"DEPOT_DOWNLOADER_CMD_PATH: {self.depot_downloader_cmd_path}\n"
            f"FORCE_DOWNLOAD: {self.force_download}\n"
            f"STEAM_USERNAME: {self.steam_username}\n"
            #f"STEAM_PASSWORD: {self.steam_password}\n"
            f"STEAM_GAME_DOWNLOAD_PATH: {self.steam_game_download_path}\n"
            
            f"SHIPPING_CMD_PATH: {self.shipping_cmd_path}\n"
            f"DUMPER7_OUTPUT_DIR: {self.dumper7_output_dir}\n"

            f"OUTPUT_MAPPER_PATH: {self.output_mapper_path}\n"
            f"OUTPUT_DATA_DIR: {self.output_data_dir}\n"
        )

    def __str__(self):
        return f"Params(export_path={self.export_path}, game_name={self.game_name}, log_level={self.log_level})"
    
# Helper to initialize PARAMS with direct args if available
def init_params(log_level=None, output_data_dir=None, output_mapper_path=None):
    global PARAMS
    PARAMS = Params(log_level=log_level, output_data_dir=output_data_dir, output_mapper_path=output_mapper_path)
    return PARAMS

def is_truthy(string):
    TRUE_THO = [
        True,
        'true',
        'True',
        'TRUE',
        't',
        'T',
        1,
    ]
    return string in TRUE_THO


###############################
#             FILE            #
###############################

def normalize_path(path: str) -> str:
    """Normalize a file path to use forward slashes for cross-platform consistency."""
    # Use os.path.normpath to normalize the path properly for the current platform
    # This ensures drive letters and absolute paths are handled correctly
    normalized = os.path.normpath(path)
    # Only convert backslashes to forward slashes for display consistency in tests
    # but preserve the platform-specific absolute path characteristics
    return normalized.replace('\\', '/')


###############################
#           Process           #
###############################

def run_process(params, name='', timeout=60*60, background=False): #times out after 1hr
    """Runs a subprocess with the given parameters and logs its output line by line

    Args:
        params (list[str] | str): The command and arguments to execute
        name (str, optional): An optional name to identify the process in logs. Defaults to ''
        timeout (int, optional): Maximum time to wait for process completion in seconds. Defaults to 3600 (1 hour)
        background (bool, optional): If True, starts the process in background and returns the process object. Defaults to False.
    
    Returns:
        subprocess.Popen: If background=True, returns the process object for later management
        None: If background=False (default), waits for completion and returns None
    """
    import select
    import time
    
    process = None
    try:
        # Handle shell scripts on Windows by explicitly using bash
        if isinstance(params, str) and params.endswith('.sh') and os.name == 'nt':
            params = ['bash', params]
        elif isinstance(params, list) and len(params) > 0 and params[0].endswith('.sh') and os.name == 'nt':
            params = ['bash'] + params

        process = subprocess.Popen(  # noqa: F821
            params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # If background mode, return the process object immediately
        if background:
            logger.info(f'Started background process {name} with PID {process.pid}')
            return process

        start_time = time.time()
        
        # Read output line by line with timeout protection
        with process.stdout:
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    # Process finished, read any remaining output
                    remaining_output = process.stdout.read()
                    if remaining_output:
                        for line in remaining_output.splitlines():
                            logger.debug(f'[process: {name}] {line.strip()}')
                    break
                
                # Check timeout
                if time.time() - start_time > timeout:
                    process.terminate()
                    try:
                        process.wait(timeout=5)  # Give it 5 seconds to terminate gracefully
                    except subprocess.TimeoutExpired:
                        process.kill()  # Force kill if it doesn't terminate
                    raise Exception(f'Process {name} timed out after {timeout} seconds')
                
                # Use select on Unix-like systems for non-blocking read
                if hasattr(select, 'select') and os.name != 'nt':
                    ready, _, _ = select.select([process.stdout], [], [], 0.1)
                    if ready:
                        line = process.stdout.readline()
                        if line:
                            logger.debug(f'[process: {name}] {line.strip()}')
                        elif process.poll() is not None:
                            # Process finished and no more output
                            break
                else:
                    # Windows fallback - read with short timeout simulation
                    try:
                        line = process.stdout.readline()
                        if line:
                            logger.debug(f'[process: {name}] {line.strip()}')
                        elif process.poll() is not None:
                            # Process finished and no more output
                            break
                    except Exception:
                        # If readline fails, check if process is still running
                        if process.poll() is not None:
                            break
                        time.sleep(0.1)  # Brief pause to prevent tight loop

    except Exception as e:
        # Clean up process if it's still running
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        raise Exception(f'Failed to run {name} process', e)

    # Wait for process to complete and get exit code
    exit_code = process.wait()
    if exit_code != 0:
        raise Exception(f'Process {name} exited with code {exit_code}')
