import unittest
import sys
import os
import tempfile
import shutil
import argparse
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Add the src directory to the Python path to import options
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.options module to avoid conflicts with tests.utils
import importlib.util
spec = importlib.util.spec_from_file_location("src_options", os.path.join(src_path, "options.py"))
src_options = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_options)

Options = src_options.Options

def create_args(**kwargs):
    """Helper function to create argparse Namespace with given arguments."""
    # Convert kwargs to use underscores instead of hyphens for argparse compatibility
    converted_kwargs = {}
    for key, value in kwargs.items():
        # Convert hyphens to underscores for argparse attribute names
        attr_name = key.replace('-', '_')
        converted_kwargs[attr_name] = value
    
    return argparse.Namespace(**converted_kwargs)


class TestOptions(unittest.TestCase):
    """Test cases for the Options class.
    
    The Options class handles configuration options with environment variable fallback,
    validation, and logging setup.
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

    @patch.object(src_options, 'logger')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_options_init_with_no_args(self, mock_print, mock_logger):
        """Test Options initialization with no arguments (should use defaults)."""
        # Mock logger.add and logger.remove to avoid actual logging setup
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options()
        
        # Should have all default values
        self.assertEqual(options.log_level, "DEBUG")  # Default from schema
        self.assertFalse(options.should_download_dependencies)  # Default False, but may be True due to ease-of-use logic
        self.assertTrue(hasattr(options, 'should_download_steam_game'))

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_init_with_args(self, mock_print, mock_logger):
        """Test Options initialization with argparse arguments."""
        # Mock logger methods
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        args = create_args(
            log_level="INFO",
            should_download_dependencies=True,
            force_download_dependencies=True,
            manifest_id="12345",
            should_download_steam_game=True,
            force_steam_download=False,
            steam_username="testuser",
            steam_password="testpass",
            steam_game_download_dir=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            force_get_mapper=True,
            should_batch_export=True,
            output_data_dir=self.output_dir,
            force_export=False
        )
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # Verify all options are set correctly
        self.assertEqual(options.log_level, "INFO")
        self.assertTrue(options.should_download_dependencies)
        self.assertTrue(options.force_download_dependencies)
        self.assertEqual(options.manifest_id, "12345")
        self.assertTrue(options.should_download_steam_game)
        self.assertFalse(options.force_steam_download)
        self.assertEqual(options.steam_username, "testuser")
        self.assertEqual(options.steam_password, "testpass")
        self.assertEqual(str(options.steam_game_download_dir), self.steam_dir)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_environment_variable_fallback(self, mock_print, mock_logger):
        """Test Options falls back to environment variables when args not provided."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        env_vars = {
            'LOG_LEVEL': 'ERROR',
            'SHOULD_DOWNLOAD_DEPENDENCIES': 'True',
            'FORCE_DOWNLOAD_DEPENDENCIES': 'True',
            'MANIFEST_ID': '67890',
            'SHOULD_DOWNLOAD_STEAM_GAME': 'True',
            'FORCE_STEAM_DOWNLOAD': 'False',
            'STEAM_USERNAME': 'envuser',
            'STEAM_PASSWORD': 'envpass',
            'STEAM_GAME_DOWNLOAD_DIR': self.steam_dir,
            'SHOULD_GET_MAPPER': 'True',
            'DUMPER7_OUTPUT_DIR': self.dumper_dir,
            'OUTPUT_MAPPER_FILE': os.path.join(self.mapper_dir, "env.usmap"),
            'FORCE_GET_MAPPER': 'False',
            'SHOULD_BATCH_EXPORT': 'True',
            'OUTPUT_DATA_DIR': self.output_dir,
            'FORCE_EXPORT': 'True'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            options = Options()
        
        # Verify environment variables are used
        self.assertEqual(options.log_level, "ERROR")
        self.assertTrue(options.should_download_dependencies)
        self.assertTrue(options.force_download_dependencies)
        self.assertEqual(options.manifest_id, "67890")
        self.assertTrue(options.should_download_steam_game)
        self.assertFalse(options.force_steam_download)
        self.assertEqual(options.steam_username, "envuser")
        self.assertEqual(options.steam_password, "envpass")
        self.assertFalse(options.force_get_mapper)
        self.assertTrue(options.force_export)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_args_override_environment(self, mock_print, mock_logger):
        """Test that command line arguments override environment variables."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        env_vars = {
            'LOG_LEVEL': 'WARNING',
            'STEAM_USERNAME': 'envuser',
            'STEAM_PASSWORD': 'envpass',
            'SHOULD_DOWNLOAD_STEAM_GAME': 'True',
            'STEAM_GAME_DOWNLOAD_DIR': self.steam_dir,
            'SHOULD_GET_MAPPER': 'True',
            'DUMPER7_OUTPUT_DIR': self.dumper_dir,
            'OUTPUT_MAPPER_FILE': os.path.join(self.mapper_dir, "test.usmap"),
            'SHOULD_BATCH_EXPORT': 'True',
            'OUTPUT_DATA_DIR': self.output_dir
        }
        
        args = create_args(
            log_level="CRITICAL",
            steam_username="arguser",
            should_download_steam_game=True,
            should_get_mapper=True,
            should_batch_export=True,
            force_export=False
        )
        
        with patch.dict(os.environ, env_vars, clear=True):
            options = Options(args)
        
        # Arguments should override environment
        self.assertEqual(options.log_level, "CRITICAL")  # Overridden
        self.assertEqual(options.steam_username, "arguser")  # Overridden
        self.assertEqual(options.steam_password, "envpass")  # From env
        self.assertFalse(options.force_export)  # Overridden

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_type_conversion_from_env(self, mock_print, mock_logger):
        """Test proper type conversion from environment variables."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        env_vars = {
            'LOG_LEVEL': 'DEBUG',
            'SHOULD_DOWNLOAD_DEPENDENCIES': 'true',  # String boolean
            'FORCE_DOWNLOAD_DEPENDENCIES': 'false',  # String boolean
            'STEAM_GAME_DOWNLOAD_DIR': self.steam_dir,  # Should become Path
            'SHOULD_GET_MAPPER': 'True',
            'DUMPER7_OUTPUT_DIR': self.dumper_dir,  # Should become Path
            'OUTPUT_MAPPER_FILE': os.path.join(self.mapper_dir, "test.usmap"),  # Should become Path
            'SHOULD_BATCH_EXPORT': 'True',
            'OUTPUT_DATA_DIR': self.output_dir  # Should become Path
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            options = Options()
        
        # Verify type conversions
        self.assertIsInstance(options.should_download_dependencies, bool)
        self.assertTrue(options.should_download_dependencies)  # 'true' -> True
        self.assertIsInstance(options.force_download_dependencies, bool)
        self.assertFalse(options.force_download_dependencies)  # 'false' -> False
        self.assertIsInstance(options.steam_game_download_dir, Path)
        self.assertIsInstance(options.dumper7_output_dir, Path)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_literal_type_validation(self, mock_print, mock_logger):
        """Test Literal type validation for log level."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        # Valid log level - provide all required options for steam section
        valid_env = {
            'LOG_LEVEL': 'INFO',
            'SHOULD_DOWNLOAD_STEAM_GAME': 'True',
            'STEAM_USERNAME': 'testuser',
            'STEAM_PASSWORD': 'testpass',
            'STEAM_GAME_DOWNLOAD_DIR': self.steam_dir,
            'SHOULD_GET_MAPPER': 'True',
            'DUMPER7_OUTPUT_DIR': self.dumper_dir,
            'OUTPUT_MAPPER_FILE': os.path.join(self.mapper_dir, "test.usmap"),
            'SHOULD_BATCH_EXPORT': 'True',
            'OUTPUT_DATA_DIR': self.output_dir
        }
        
        with patch.dict(os.environ, valid_env, clear=True):
            options = Options()
            self.assertEqual(options.log_level, "INFO")
        
        # Invalid log level should fall back to default
        invalid_env = valid_env.copy()
        invalid_env['LOG_LEVEL'] = 'INVALID_LEVEL'
        
        with patch.dict(os.environ, invalid_env, clear=True):
            options = Options()
            self.assertEqual(options.log_level, "DEBUG")  # Should fall back to default

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_missing_required_section_options_raises_error(self, mock_print, mock_logger):
        """Test that missing required section options raise ValueError."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        # Enable should_download_steam_game but don't provide required section options
        args = create_args(
            should_download_steam_game=True,
            # Missing: steam_username, steam_password, steam_game_download_dir
            should_get_mapper=True,
            should_batch_export=True
        )
        
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                Options(args)
            
            error_message = str(context.exception)
            self.assertIn("following options must be provided", error_message)
            self.assertIn("STEAM_USERNAME", error_message)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_should_flags_explicit_false(self, mock_print, mock_logger):
        """Test that should_* options can be explicitly set to False."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        # Provide only non-should arguments and turn off all should flags
        args = create_args(
            log_level="INFO",
            should_download_dependencies=False,
            should_download_steam_game=False,
            should_get_mapper=False,
            should_batch_export=False
        )
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # When explicitly set to False, they should remain False
        self.assertFalse(options.should_download_dependencies)
        self.assertFalse(options.should_download_steam_game)
        self.assertFalse(options.should_get_mapper)
        self.assertFalse(options.should_batch_export)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_behavior_with_minimal_args(self, mock_print, mock_logger):
        """Test Options behavior with minimal arguments provided."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        # Just test that we can create options with minimal args
        # and that the schema defaults are used appropriately
        args = create_args(
            log_level="INFO",
            should_download_dependencies=False,
            should_download_steam_game=False,
            should_get_mapper=False,
            should_batch_export=False
        )
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # Verify the provided args are respected
        self.assertEqual(options.log_level, "INFO")
        self.assertFalse(options.should_download_dependencies)
        self.assertFalse(options.should_download_steam_game)
        self.assertFalse(options.should_get_mapper)
        self.assertFalse(options.should_batch_export)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_attribute_name_conversion(self, mock_print, mock_logger):
        """Test that schema keys are converted to lowercase attribute names."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        args = create_args(
            log_level="DEBUG",
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test",
            steam_game_download_dir=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # Test that schema keys (UPPER_CASE) become lowercase attributes
        self.assertTrue(hasattr(options, 'log_level'))  # LOG_LEVEL -> log_level
        self.assertTrue(hasattr(options, 'should_download_steam_game'))  # SHOULD_DOWNLOAD_STEAM_GAME -> should_download_steam_game
        self.assertTrue(hasattr(options, 'steam_username'))  # STEAM_USERNAME -> steam_username

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_validate_method_called(self, mock_print, mock_logger):
        """Test that validate method is called during initialization."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        args = create_args(
            log_level="DEBUG",
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test",
            steam_game_download_dir=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Options, 'validate') as mock_validate:
                options = Options(args)
                mock_validate.assert_called_once()

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_log_method_called(self, mock_print, mock_logger):
        """Test that log method is called during initialization."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        args = create_args(
            log_level="DEBUG",
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test",
            steam_game_download_dir=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Options, 'log') as mock_log:
                options = Options(args)
                mock_log.assert_called_once()

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_logger_setup(self, mock_print, mock_logger):
        """Test that logger is properly set up during initialization."""
        # Mock logger methods to capture calls
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        args = create_args(
            log_level="INFO",
            should_download_steam_game=True,
            steam_username="test",
            steam_password="test",
            steam_game_download_dir=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # Verify logger setup was called
        mock_logger.remove.assert_called()
        self.assertTrue(mock_logger.add.called)
        
        # Verify log level was set correctly
        self.assertEqual(options.log_level, "INFO")

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_sensitive_data_logging(self, mock_print, mock_logger):
        """Test that sensitive data is hidden in logs."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        mock_logger.info = Mock()
        
        args = create_args(
            log_level="DEBUG",
            should_download_steam_game=True,
            steam_username="testuser",
            steam_password="secret_password",  # This should be hidden
            steam_game_download_dir=self.steam_dir,
            should_get_mapper=True,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=os.path.join(self.mapper_dir, "test.usmap"),
            should_batch_export=True,
            output_data_dir=self.output_dir
        )
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # Check that logger.info was called with log lines
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        
        # Password should be hidden
        self.assertIn("***HIDDEN***", log_call_args)
        self.assertNotIn("secret_password", log_call_args)
        # Username should be visible
        self.assertIn("testuser", log_call_args)

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_empty_string_handling(self, mock_print, mock_logger):
        """Test handling of empty strings from environment variables."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        # Test with all should flags disabled to avoid validation errors
        env_vars = {
            'MANIFEST_ID': '',  # Empty string should be converted appropriately  
            'SHOULD_DOWNLOAD_DEPENDENCIES': 'False',
            'SHOULD_DOWNLOAD_STEAM_GAME': 'False',
            'SHOULD_GET_MAPPER': 'False', 
            'SHOULD_BATCH_EXPORT': 'False'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            options = Options()
        
        # Empty strings should be preserved for string types
        self.assertEqual(options.manifest_id, "")

    @patch.object(src_options, 'logger')
    @patch('builtins.print')
    def test_options_process_schema_method(self, mock_print, mock_logger):
        """Test the _process_schema method functionality."""
        mock_logger.add = Mock()
        mock_logger.remove = Mock()
        
        # Create a minimal test case
        args = create_args(log_level="WARNING")
        
        with patch.dict(os.environ, {}, clear=True):
            options = Options(args)
        
        # Verify the method processed the schema correctly
        self.assertEqual(options.log_level, "WARNING")
        
        # Verify print was called with processing message
        mock_print.assert_called()
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("Processing schema with args_dict:" in str(call) for call in print_calls))


if __name__ == '__main__':
    unittest.main()