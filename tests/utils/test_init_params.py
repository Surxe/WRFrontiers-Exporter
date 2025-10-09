import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, Mock

# Add the src directory to the Python path to import utils
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.utils module to avoid conflicts with tests.utils
import importlib.util
spec = importlib.util.spec_from_file_location("src_utils", os.path.join(src_path, "utils.py"))
src_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_utils)

Params = src_utils.Params
init_params = src_utils.init_params


class TestInitParams(unittest.TestCase):
    """Test cases for the init_params function.
    
    The init_params function is a factory function that creates a Params object
    with provided arguments, falling back to environment variables.
    """

    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.steam_dir = os.path.join(self.temp_dir, "steam")
        self.dumper_dir = os.path.join(self.temp_dir, "dumper")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.mapper_dir = os.path.join(self.temp_dir, "mapper")
        
        # Create required directories
        os.makedirs(self.steam_dir)
        os.makedirs(self.dumper_dir)
        os.makedirs(self.output_dir)
        os.makedirs(self.mapper_dir)

    def tearDown(self):
        """Clean up temporary directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {}, clear=True)
    def test_init_params_with_all_arguments(self):
        """Test init_params creates Params with all provided arguments."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        params = init_params(
            log_level="INFO",
            force_download_dependencies=True,
            manifest_id="12345",
            force_steam_download=True,
            steam_username="testuser",
            steam_password="testpass",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            force_get_mapper=False,
            output_data_dir=self.output_dir,
            force_export=False,
            skip_dependencies=True,
            skip_steam_update=True,
            skip_mapper=True,
            skip_batch_export=True
        )
        
        # Verify all parameters are set correctly
        self.assertEqual(params.log_level, "INFO")
        self.assertTrue(params.force_download_dependencies)
        self.assertEqual(params.manifest_id, "12345")
        self.assertTrue(params.force_steam_download)
        self.assertEqual(params.steam_username, "testuser")
        self.assertEqual(params.steam_password, "testpass")
        self.assertEqual(params.steam_game_download_path, self.steam_dir)
        self.assertEqual(params.dumper7_output_dir, self.dumper_dir)
        self.assertEqual(params.output_mapper_file, mapper_file)
        self.assertFalse(params.force_get_mapper)
        self.assertEqual(params.output_data_dir, self.output_dir)
        self.assertFalse(params.force_export)
        self.assertTrue(params.skip_dependencies)
        self.assertTrue(params.skip_steam_update)
        self.assertTrue(params.skip_mapper)
        self.assertTrue(params.skip_batch_export)

    @patch.dict(os.environ, {
        'LOG_LEVEL': 'ERROR',
        'FORCE_DOWNLOAD_DEPENDENCIES': 'True',
        'MANIFEST_ID': '67890',
        'FORCE_STEAM_DOWNLOAD': 'False',
        'STEAM_USERNAME': 'envuser',
        'STEAM_PASSWORD': 'envpass',
        'FORCE_GET_MAPPER': 'False',
        'FORCE_EXPORT': 'True',
        'SKIP_DEPENDENCIES': 'True',
        'SKIP_STEAM_UPDATE': 'False',
        'SKIP_MAPPER': 'True',
        'SKIP_BATCH_EXPORT': 'False'
    })
    def test_init_params_with_environment_fallback(self, mock_steam_dir, mock_dumper_dir, mock_mapper_file, mock_output_dir):
        """Test init_params falls back to environment variables."""
        # Mock the required paths in environment
        with patch.dict(os.environ, {
            'STEAM_GAME_DOWNLOAD_PATH': mock_steam_dir,
            'DUMPER7_OUTPUT_DIR': mock_dumper_dir,
            'OUTPUT_MAPPER_FILE': mock_mapper_file,
            'OUTPUT_DATA_DIR': mock_output_dir
        }, clear=False):
            params = init_params()
            
            # Verify environment variables are used
            self.assertEqual(params.log_level, "ERROR")
            self.assertTrue(params.force_download_dependencies)
            self.assertEqual(params.manifest_id, "67890")
            self.assertFalse(params.force_steam_download)
            self.assertEqual(params.steam_username, "envuser")
            self.assertEqual(params.steam_password, "envpass")
            self.assertFalse(params.force_get_mapper)
            self.assertTrue(params.force_export)
            self.assertTrue(params.skip_dependencies)
            self.assertFalse(params.skip_steam_update)
            self.assertTrue(params.skip_mapper)
            self.assertFalse(params.skip_batch_export)

    @patch.dict(os.environ, {
        'LOG_LEVEL': 'WARNING',
        'STEAM_USERNAME': 'envuser',
        'STEAM_PASSWORD': 'envpass'
    })
    def test_init_params_argument_override_environment(self, mock_steam_dir, mock_dumper_dir, mock_mapper_file, mock_output_dir):
        """Test init_params arguments override environment variables."""
        with patch.dict(os.environ, {
            'STEAM_GAME_DOWNLOAD_PATH': mock_steam_dir,
            'DUMPER7_OUTPUT_DIR': mock_dumper_dir,
            'OUTPUT_MAPPER_FILE': mock_mapper_file,
            'OUTPUT_DATA_DIR': mock_output_dir
        }, clear=False):
            params = init_params(
                log_level="CRITICAL",
                steam_username="arguser",
                force_export=True,
                skip_dependencies=False
            )
            
            # Arguments should override environment
            self.assertEqual(params.log_level, "CRITICAL")  # Overridden
            self.assertEqual(params.steam_username, "arguser")  # Overridden
            self.assertEqual(params.steam_password, "envpass")  # From env
            self.assertTrue(params.force_export)  # Overridden
            self.assertFalse(params.skip_dependencies)  # Overridden

    def test_init_params_returns_params_object(self):
        """Test init_params returns a Params instance."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        params = init_params(
            log_level="DEBUG",
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            output_data_dir=self.output_dir
        )
        
        self.assertIsInstance(params, Params)

    def test_init_params_sets_global_params(self):
        """Test init_params sets the global PARAMS variable."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        params = init_params(
            log_level="DEBUG",
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            output_data_dir=self.output_dir
        )
        
        # Check that global PARAMS is set
        self.assertEqual(src_utils.PARAMS, params)

    def test_init_params_with_none_values(self):
        """Test init_params handles None values correctly."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        # Provide some args as None to test fallback behavior
        params = init_params(
            log_level=None,  # Should use default
            steam_username="test",
            steam_password="test", 
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            output_data_dir=self.output_dir,
            force_export=None,  # Should use default
            skip_dependencies=None  # Should use default
        )
        
        # None values should trigger fallback to environment/defaults
        self.assertEqual(params.log_level, "DEBUG")  # Default
        self.assertEqual(params.steam_username, "test")
        self.assertFalse(params.force_export)  # Default False (env var 'False' in test)
        self.assertFalse(params.skip_dependencies)  # Default False

    def test_init_params_partial_arguments(self):
        """Test init_params with only some arguments provided."""
        params = init_params(
            log_level="INFO",
            steam_username="partialtest",
            steam_password="partialpass",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            output_data_dir=self.output_dir
        )
        
        # Provided arguments should be set
        self.assertEqual(params.log_level, "INFO")
        self.assertEqual(params.steam_username, "partialtest")
        
        # Unprovided arguments should use defaults
        self.assertFalse(params.force_download_dependencies)  # Default False
        self.assertFalse(params.force_get_mapper)  # Default False (env var 'False' in test)
        self.assertFalse(params.skip_dependencies)  # Default False


# Mock the file system dependencies for environment tests
def mock_paths_setup(test_func):
    """Decorator to set up mock paths for environment tests."""
    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            steam_dir = os.path.join(temp_dir, "steam")
            dumper_dir = os.path.join(temp_dir, "dumper") 
            output_dir = os.path.join(temp_dir, "output")
            mapper_file = os.path.join(temp_dir, "mapper", "test.usmap")
            
            os.makedirs(steam_dir)
            os.makedirs(dumper_dir)
            os.makedirs(output_dir)
            os.makedirs(os.path.dirname(mapper_file))
            
            return test_func(*args, steam_dir, dumper_dir, mapper_file, output_dir, **kwargs)
    return wrapper

# Apply decorator to environment tests
TestInitParams.test_init_params_with_environment_fallback = mock_paths_setup(TestInitParams.test_init_params_with_environment_fallback)
TestInitParams.test_init_params_argument_override_environment = mock_paths_setup(TestInitParams.test_init_params_argument_override_environment)


if __name__ == '__main__':
    unittest.main()