import unittest
import sys
import os
import tempfile
import shutil
import argparse
from unittest.mock import patch, Mock

# Add the src directory to the Python path to import utils
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.options module to avoid conflicts with tests.utils
import importlib.util
spec = importlib.util.spec_from_file_location("src_options", os.path.join(src_path, "options.py"))
src_options = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_options)

Options = src_options.Options
init_options = src_options.init_options

def create_args(**kwargs):
    """Helper function to create argparse Namespace with given arguments."""
    # Convert kwargs to use underscores instead of hyphens for argparse compatibility
    converted_kwargs = {}
    for key, value in kwargs.items():
        # Convert hyphens to underscores for argparse attribute names
        attr_name = key.replace('-', '_')
        converted_kwargs[attr_name] = value
    
    return argparse.Namespace(**converted_kwargs)


class TestInitOptions(unittest.TestCase):
    """Test cases for the init_options function.
    
    The init_options function is a factory function that creates a Options object
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
    def test_init_options_with_all_arguments(self):
        """Test init_options creates Options with all provided arguments."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        args = create_args(
            log_level="INFO",
            should_download_dependencies=True,
            force_download_dependencies=True,
            manifest_id="12345",
            should_download_steam_game=True,
            force_steam_download=True,
            steam_username="testuser",
            steam_password="testpass",
            steam_game_download_path=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            force_get_mapper=False,
            should_batch_export=True,
            output_data_dir=self.output_dir,
            force_export=False
        )
        options = init_options(args)
        
        # Verify all options are set correctly
        self.assertEqual(options.log_level, "INFO")
        self.assertTrue(options.should_download_dependencies)
        self.assertTrue(options.force_download_dependencies)
        self.assertEqual(options.manifest_id, "12345")
        self.assertTrue(options.should_download_steam_game)
        self.assertTrue(options.force_steam_download)
        self.assertEqual(options.steam_username, "testuser")
        self.assertEqual(options.steam_password, "testpass")
        self.assertEqual(str(options.steam_game_download_path), self.steam_dir)
        self.assertTrue(options.should_get_mapper)
        self.assertEqual(str(options.dumper7_output_dir), self.dumper_dir)
        self.assertEqual(str(options.output_mapper_file), mapper_file)
        self.assertFalse(options.force_get_mapper)
        self.assertTrue(options.should_batch_export)
        self.assertEqual(str(options.output_data_dir), self.output_dir)
        self.assertFalse(options.force_export)

    @patch.dict(os.environ, {
        'LOG_LEVEL': 'ERROR',
        'SHOULD_DOWNLOAD_DEPENDENCIES': 'True',
        'FORCE_DOWNLOAD_DEPENDENCIES': 'True',
        'MANIFEST_ID': '67890',
        'SHOULD_DOWNLOAD_STEAM_GAME': 'True',
        'FORCE_STEAM_DOWNLOAD': 'False',
        'STEAM_USERNAME': 'envuser',
        'STEAM_PASSWORD': 'envpass',
        'SHOULD_GET_MAPPER': 'True',
        'FORCE_GET_MAPPER': 'False',
        'SHOULD_BATCH_EXPORT': 'True',
        'FORCE_EXPORT': 'True'
    })
    def test_init_options_with_environment_fallback(self, mock_steam_dir, mock_dumper_dir, mock_mapper_file, mock_output_dir):
        """Test init_options falls back to environment variables."""
        # Mock the required paths in environment
        with patch.dict(os.environ, {
            'STEAM_GAME_DOWNLOAD_PATH': mock_steam_dir,
            'DUMPER7_OUTPUT_DIR': mock_dumper_dir,
            'OUTPUT_MAPPER_FILE': mock_mapper_file,
            'OUTPUT_DATA_DIR': mock_output_dir
        }, clear=False):
            options = init_options()
            
            # Verify environment variables are used
            self.assertEqual(options.log_level, "ERROR")
            self.assertTrue(options.should_download_dependencies)
            self.assertTrue(options.force_download_dependencies)
            self.assertEqual(options.manifest_id, "67890")
            self.assertTrue(options.should_download_steam_game)
            self.assertFalse(options.force_steam_download)
            self.assertEqual(options.steam_username, "envuser")
            self.assertEqual(options.steam_password, "envpass")
            self.assertTrue(options.should_get_mapper)
            self.assertFalse(options.force_get_mapper)
            self.assertTrue(options.should_batch_export)
            self.assertTrue(options.force_export)

    @patch.dict(os.environ, {
        'LOG_LEVEL': 'WARNING',
        'SHOULD_DOWNLOAD_STEAM_GAME': 'True',
        'STEAM_USERNAME': 'envuser',
        'STEAM_PASSWORD': 'envpass',
        'SHOULD_BATCH_EXPORT': 'True'
    })
    def test_init_options_argument_override_environment(self, mock_steam_dir, mock_dumper_dir, mock_mapper_file, mock_output_dir):
        """Test init_options arguments override environment variables."""
        with patch.dict(os.environ, {
            'STEAM_GAME_DOWNLOAD_PATH': mock_steam_dir,
            'DUMPER7_OUTPUT_DIR': mock_dumper_dir,
            'OUTPUT_MAPPER_FILE': mock_mapper_file,
            'OUTPUT_DATA_DIR': mock_output_dir
        }, clear=False):
            args = create_args(
                log_level="CRITICAL",
                should_download_steam_game=True,
                steam_username="arguser",
                should_batch_export=True,
                force_export=False
            )
            options = init_options(args)
            
            # Arguments should override environment
            self.assertEqual(options.log_level, "CRITICAL")  # Overridden
            self.assertEqual(options.steam_username, "arguser")  # Overridden
            self.assertEqual(options.steam_password, "envpass")  # From env
            self.assertFalse(options.force_export)  # Overridden

    def test_init_options_returns_options_object(self):
        """Test init_options returns a Options instance."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        args = create_args(
            log_level="DEBUG",
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        options = init_options(args)
        
        self.assertIsInstance(options, Options)

    def test_init_options_sets_global_options(self):
        """Test init_options sets the global OPTIONS variable."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        args = create_args(
            log_level="DEBUG",
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        options = init_options(args)
        
        # Check that global OPTIONS is set
        self.assertEqual(src_options.OPTIONS, options)

    @patch.dict(os.environ, {}, clear=True)  # Clear environment to test pure defaults
    def test_init_options_with_none_values(self):
        """Test init_options handles None values correctly."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        # Provide some args as None to test fallback behavior
        args = create_args(
            log_level=None,  # Should use default
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test", 
            steam_game_download_path=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            should_batch_export=True,
            output_data_dir=self.output_dir,
            force_export=None  # Should use default
        )
        options = init_options(args)
        
        # None values should trigger fallback to environment/defaults
        self.assertEqual(options.log_level, "DEBUG")  # Default
        self.assertEqual(options.steam_username, "test")
        self.assertTrue(options.force_export)  # Default True

    @patch.dict(os.environ, {}, clear=True)  # Clear environment to test pure defaults
    def test_init_options_partial_arguments(self):
        """Test init_options with only some arguments provided."""
        args = create_args(
            log_level="INFO",
            should_download_steam_game=True,
            steam_username="partialtest",
            steam_password="partialpass",
            steam_game_download_path=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        options = init_options(args)
        
        # Provided arguments should be set
        self.assertEqual(options.log_level, "INFO")
        self.assertEqual(options.steam_username, "partialtest")
        
        # Unprovided arguments should use defaults
        self.assertFalse(options.force_download_dependencies)  # Default False
        self.assertTrue(options.force_get_mapper)  # Default True


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
TestInitOptions.test_init_options_with_environment_fallback = mock_paths_setup(TestInitOptions.test_init_options_with_environment_fallback)
TestInitOptions.test_init_options_argument_override_environment = mock_paths_setup(TestInitOptions.test_init_options_argument_override_environment)


if __name__ == '__main__':
    unittest.main()