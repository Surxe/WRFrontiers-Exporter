# Utils test package

# Import all test modules for easy discovery
from . import test_is_admin
from . import test_run_process
from . import test_terminate_process_by_name
from . import test_wait_for_process_by_name
from . import test_wait_for_process_ready_for_injection
from . import test_is_truthy
from . import test_normalize_path
from . import test_clear_dir
from . import test_init_params
from . import test_params

__all__ = [
    'test_is_admin',
    'test_run_process', 
    'test_terminate_process_by_name',
    'test_wait_for_process_by_name',
    'test_wait_for_process_ready_for_injection',
    'test_is_truthy',
    'test_normalize_path',
    'test_clear_dir',
    'test_init_params',
    'test_params'
]