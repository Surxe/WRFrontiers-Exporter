from dotenv import load_dotenv

import os
import sys
import subprocess
import os
import shutil
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
                 manifest_id=None, force_steam_download=None, steam_username=None, steam_password=None, steam_game_download_path=None,
                 dumper7_output_dir=None, 
                 output_mapper_file=None, force_get_mapper=None, output_data_dir=None, force_export=None):
        
        # Use provided args if not None, else fallback to environment
        self.log_level = (log_level if log_level is not None else os.getenv('LOG_LEVEL', 'DEBUG')).upper()
        
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
        if not os.path.exists(self.output_data_dir):
            raise ValueError(f"OUTPUT_DATA_DIR '{self.output_data_dir}' does not exist.")
        
        if not isinstance(self.force_export, bool):
            raise ValueError("FORCE_EXPORT must be a boolean value (True or False).")
        
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
        )

    def __str__(self):
        return f"Params(export_path={self.export_path}, game_name={self.game_name}, log_level={self.log_level})"
    
# Helper to initialize PARAMS with direct args if available
def init_params(log_level=None, manifest_id=None, output_data_dir=None, output_mapper_file=None, force_export=None):
    global PARAMS
    PARAMS = Params(log_level=log_level, manifest_id=manifest_id, output_data_dir=output_data_dir, output_mapper_file=output_mapper_file, force_export=force_export)
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

def clear_dir(dir_path: str) -> None:
    """Clear directory contents but keep the directory itself"""
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

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

def wait_for_process_by_name(process_name, timeout=60):
    """Wait for a process with the given name to start
    
    Args:
        process_name (str): The name of the process to wait for (e.g., "notepad.exe")
        timeout (int, optional): Maximum time to wait in seconds. Defaults to 60.
    
    Returns:
        int: The PID of the found process
    
    Raises:
        Exception: If process not found within timeout
    """
    import time
    
    start_time = time.time()
    attempt_count = 0
    
    while time.time() - start_time < timeout:
        attempt_count += 1
        
        # Use tasklist on Windows to check for running processes
        if os.name == 'nt':
            try:
                result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                      capture_output=True, text=True, check=True)
                
                # Debug logging every 2 attempts (10 seconds)
                if attempt_count % 2 == 1:
                    logger.debug(f"Attempt {attempt_count}: Looking for {process_name}")
                    logger.debug(f"Tasklist output: {result.stdout[:200]}...")  # First 200 chars
                
                # Check if the process name appears in output (handle truncated names)
                # For "WRFrontiers-Win64-Shipping.exe", look for "wrfrontiers-win64-ship" (truncated version)
                process_base_name = process_name.replace('.exe', '').lower()
                process_short_name = process_base_name[:20].lower()  # First 20 chars, typical truncation length
                
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line_lower = line.lower()
                    # Skip header lines
                    if 'image name' in line_lower or '=====' in line_lower:
                        continue
                        
                    # Check for process name match (full, base, or truncated)
                    if (process_name.lower() in line_lower or 
                        process_base_name in line_lower or 
                        process_short_name in line_lower):
                        
                        parts = line.split()
                        if len(parts) >= 2 and parts[1].isdigit():
                            pid = parts[1]
                            logger.info(f"Process {process_name} detected (PID: {pid}) - matched in line: {line.strip()}")
                            return int(pid)
                
                # Also try without the filter to see all processes (for debugging)
                if attempt_count % 6 == 1:  # Every 30 seconds
                    logger.debug("Checking all running processes for debugging...")
                    all_result = subprocess.run(['tasklist'], capture_output=True, text=True, check=True)
                    matching_lines = [line for line in all_result.stdout.split('\n') 
                                    if 'wrfrontiers' in line.lower() or 'shipping' in line.lower()]
                    if matching_lines:
                        logger.debug(f"Found WRFrontiers-related processes: {matching_lines}")
                    else:
                        logger.debug("No WRFrontiers-related processes found in full tasklist")
                        
            except (subprocess.CalledProcessError, ValueError) as e:
                if attempt_count % 2 == 1:
                    logger.debug(f"Tasklist error: {e}")
        else:
            # Unix-like systems
            try:
                result = subprocess.run(['pgrep', '-f', process_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    pid = int(result.stdout.strip().split('\n')[0])
                    logger.info(f"Process {process_name} detected (PID: {pid})")
                    return pid
            except (subprocess.CalledProcessError, ValueError):
                pass
        
        time.sleep(5)  # Wait 5 seconds between attempts (1/5th as often)
    
    raise Exception(f"Process {process_name} not found within {timeout} seconds")

def terminate_process_by_name(process_name):
    """Terminate a process by name
    
    Args:
        process_name (str): The name of the process to terminate
    
    Returns:
        bool: True if process was found and terminated, False otherwise
    """
    if os.name == 'nt':
        # Windows
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', process_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Terminated process {process_name}")
                return True
            else:
                logger.warning(f"Failed to terminate {process_name}: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error terminating {process_name}: {e}")
            return False
    else:
        # Unix-like systems
        try:
            result = subprocess.run(['pkill', '-f', process_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Terminated process {process_name}")
                return True
            else:
                logger.warning(f"Failed to terminate {process_name}")
                return False
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error terminating {process_name}: {e}")
            return False

def is_admin():
    """Check if the current process is running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def wait_for_process_ready_for_injection(process_name, initialization_time=30):
    """Wait for a process to be ready for DLL injection
    
    This function waits for the process to not only exist, but also be in a state
    where DLL injection is likely to succeed (fully loaded, not just starting up).
    
    Args:
        process_name (str): The name of the process to wait for (e.g., "notepad.exe")
        initialization_time (int, optional): Time in seconds to wait after process is found. Defaults to 30.
    
    Returns:
        int: The PID of the ready process
    
    Raises:
        Exception: If process not ready within timeout or died during initialization
    """
    import time
    
    # First wait for the process to exist
    logger.info(f"Waiting for {process_name} to start...")
    pid = wait_for_process_by_name(process_name, timeout=60)
    
    # Then wait additional time for it to fully initialize
    logger.info(f"Process {process_name} found (PID: {pid}), waiting for full initialization...")
    
    # Wait in chunks, checking if process is still alive
    check_interval = 5  # check every 5 seconds
    
    for i in range(0, initialization_time, check_interval):
        time.sleep(check_interval)
        
        # Verify process is still running
        if os.name == 'nt':
            try:
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                      capture_output=True, text=True, check=True)
                if str(pid) not in result.stdout:
                    raise Exception(f"Process {process_name} (PID: {pid}) died during initialization")
            except subprocess.CalledProcessError:
                raise Exception(f"Failed to check if process {process_name} is still running")
        
        elapsed = i + check_interval
        logger.info(f"Initialization progress: {elapsed}/{initialization_time} seconds...")
    
    logger.info(f"Process {process_name} should now be ready for injection")
    return pid

def terminate_process_object(process, name=''):
    """Terminate a subprocess.Popen process object
    
    Args:
        process (subprocess.Popen): The process object to terminate
        name (str, optional): Name for logging purposes
    
    Returns:
        bool: True if successfully terminated, False otherwise
    """
    if process and process.poll() is None:
        try:
            process.terminate()
            try:
                process.wait(timeout=10)
                logger.info(f"Terminated process {name} (PID: {process.pid})")
                return True
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                logger.info(f"Force killed process {name} (PID: {process.pid})")
                return True
        except Exception as e:
            logger.error(f"Failed to terminate process {name}: {e}")
            return False
    return False