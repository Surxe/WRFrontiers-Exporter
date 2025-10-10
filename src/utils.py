from dotenv import load_dotenv

import os
import subprocess
import os
import shutil
from loguru import logger
load_dotenv()

###############################
#           Options            #
###############################

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

def run_process(options, name='', timeout=60*60, background=False): #times out after 1hr
    """Runs a subprocess with the given options and logs its output line by line

    Args:
        options (list[str] | str): The command and arguments to execute
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
        if isinstance(options, str) and options.endswith('.sh') and os.name == 'nt':
            options = ['bash', options]
        elif isinstance(options, list) and len(options) > 0 and options[0].endswith('.sh') and os.name == 'nt':
            options = ['bash'] + options

        process = subprocess.Popen(  # noqa: F821
            options, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
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