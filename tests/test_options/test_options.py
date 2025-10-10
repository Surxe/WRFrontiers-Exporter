import unittest
import sys
import os
import tempfile
import shutil
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


class TestOptions(unittest.TestCase):
    """Test cases for the Options class initialization and validation.
    
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

    @patch.object(src_utils, 'logger')
    def test_options_init_with_valid_args(self, mock_logger):
        """Test Options initialization with all valid arguments."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        options = Options(
            log_level="INFO",
            force_download_dependencies=True,
            manifest_id="12345",
            force_steam_download=False,
            steam_username="testuser",
            steam_password="testpass",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            force_get_mapper=True,
            output_data_dir=self.output_dir,
            force_export=False,
            skip_dependencies=True,
            skip_steam_update=False,
            skip_mapper=True,
            skip_batch_export=False
        )
        
        # Verify all options are set correctly
        self.assertEqual(options.log_level, "INFO")
        self.assertTrue(options.force_download_dependencies)
        self.assertEqual(options.manifest_id, "12345")
        self.assertFalse(options.force_steam_download)
        self.assertEqual(options.steam_username, "testuser")
        self.assertEqual(options.steam_password, "testpass")
        self.assertEqual(options.steam_game_download_path, self.steam_dir)
        self.assertEqual(options.dumper7_output_dir, self.dumper_dir)
        self.assertEqual(options.output_mapper_file, mapper_file)
        self.assertTrue(options.force_get_mapper)
        self.assertEqual(options.output_data_dir, self.output_dir)
        self.assertFalse(options.force_export)
        self.assertTrue(options.skip_dependencies)
        self.assertFalse(options.skip_steam_update)
        self.assertTrue(options.skip_mapper)
        self.assertFalse(options.skip_batch_export)

    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'STEAM_USERNAME': 'envuser',
        'STEAM_PASSWORD': 'envpass'
    })
    @patch.object(src_utils, 'logger')
    def test_options_init_with_environment_fallback(self, mock_logger):
        """Test Options initialization falls back to environment variables."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        with patch.dict(os.environ, {
            'STEAM_GAME_DOWNLOAD_PATH': self.steam_dir,
            'DUMPER7_OUTPUT_DIR': self.dumper_dir,
            'OUTPUT_MAPPER_FILE': mapper_file,
            'OUTPUT_DATA_DIR': self.output_dir
        }, clear=False):
            options = Options()
            
            # Should use environment variables
            self.assertEqual(options.log_level, "DEBUG")
            self.assertEqual(options.steam_username, "envuser")
            self.assertEqual(options.steam_password, "envpass")

    @patch.object(src_utils, 'logger')
    def test_options_validate_invalid_log_level(self, mock_logger):
        """Test Options validation fails for invalid log level."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="INVALID",
                steam_username="test",
                steam_password="test",
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=mapper_file,
                output_data_dir=self.output_dir
            )
        
        self.assertIn("LOG_LEVEL INVALID must be one of", str(context.exception))

    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    @patch.object(src_utils, 'logger')
    def test_options_validate_missing_steam_username(self, mock_logger):
        """Test Options validation fails for missing steam username."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="DEBUG",
                steam_username=None,  # Will fallback to empty env var
                steam_password="test",
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=mapper_file,
                output_data_dir=self.output_dir
            )
        
        self.assertIn("STEAM_USERNAME environment variable is not set", str(context.exception))

    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    @patch.object(src_utils, 'logger')
    def test_options_validate_missing_steam_password(self, mock_logger):
        """Test Options validation fails for missing steam password."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="DEBUG",
                steam_username="test",
                steam_password=None,  # Will fallback to empty env var
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=mapper_file,
                output_data_dir=self.output_dir
            )
        
        self.assertIn("STEAM_PASSWORD environment variable is not set", str(context.exception))

    @patch.object(src_utils, 'logger')
    def test_options_validate_nonexistent_steam_path(self, mock_logger):
        """Test Options validation fails for non-existent steam path."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="DEBUG",
                steam_username="test",
                steam_password="test",
                steam_game_download_path=nonexistent_path,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=mapper_file,
                output_data_dir=self.output_dir
            )
        
        self.assertIn("does not exist", str(context.exception))

    @patch.object(src_utils, 'logger')
    def test_options_validate_nonexistent_dumper_dir(self, mock_logger):
        """Test Options validation fails for non-existent dumper directory."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="DEBUG",
                steam_username="test",
                steam_password="test",
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=nonexistent_path,
                output_mapper_file=mapper_file,
                output_data_dir=self.output_dir
            )
        
        self.assertIn("DUMPER7_OUTPUT_DIR", str(context.exception))
        self.assertIn("does not exist", str(context.exception))

    @patch.object(src_utils, 'logger')
    def test_options_validate_invalid_mapper_parent_dir(self, mock_logger):
        """Test Options validation fails when mapper file parent directory doesn't exist."""
        nonexistent_mapper = os.path.join(self.temp_dir, "nonexistent", "test.usmap")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="DEBUG",
                steam_username="test",
                steam_password="test",
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=nonexistent_mapper,
                output_data_dir=self.output_dir
            )
        
        self.assertIn("Parent directory for OUTPUT_MAPPER_FILE", str(context.exception))

    @patch.object(src_utils, 'logger')
    def test_options_validate_invalid_output_data_parent_dir(self, mock_logger):
        """Test Options validation fails when output data directory parent doesn't exist."""
        nonexistent_output = os.path.join(self.temp_dir, "nonexistent", "output")
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        with self.assertRaises(ValueError) as context:
            Options(
                log_level="DEBUG",
                steam_username="test",
                steam_password="test",
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=mapper_file,
                output_data_dir=nonexistent_output
            )
        
        self.assertIn("Parent directory for OUTPUT_DATA_DIR does not exist", str(context.exception))

    @patch.object(src_utils, 'logger')
    def test_options_validate_string_boolean_conversion(self, mock_logger):
        """Test Options converts string boolean values via is_truthy."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        # Test that string values get converted to booleans via is_truthy
        options = Options(
            log_level="DEBUG",
            force_download_dependencies="maybe",  # Gets converted to False via is_truthy
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            output_data_dir=self.output_dir
        )
        
        # "maybe" should be converted to False by is_truthy
        self.assertFalse(options.force_download_dependencies)
        self.assertIsInstance(options.force_download_dependencies, bool)

    @patch.object(src_utils, 'logger')
    def test_options_empty_manifest_id_becomes_none(self, mock_logger):
        """Test Options converts empty manifest_id string to None."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        options = Options(
            log_level="DEBUG",
            manifest_id="",  # Empty string should become None
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            output_data_dir=self.output_dir
        )
        
        self.assertIsNone(options.manifest_id)

    @patch.object(src_utils, 'logger')
    def test_options_log_method_called(self, mock_logger):
        """Test that log method is called during initialization."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        Options(
            log_level="DEBUG",
            steam_username="test",
            steam_password="test",
            steam_game_download_path=self.steam_dir,
            dumper7_output_dir=self.dumper_dir,
            output_mapper_file=mapper_file,
            output_data_dir=self.output_dir
        )
        
        # Verify logger was called (log method should have been invoked)
        self.assertTrue(mock_logger.info.called)

    @patch.object(src_utils, 'logger')
    def test_options_validate_method_called(self, mock_logger):
        """Test that validate method is called during initialization."""
        mapper_file = os.path.join(self.mapper_dir, "test.usmap")
        
        # This should not raise an exception with valid options
        try:
            Options(
                log_level="DEBUG",
                steam_username="test",
                steam_password="test",
                steam_game_download_path=self.steam_dir,
                dumper7_output_dir=self.dumper_dir,
                output_mapper_file=mapper_file,
                output_data_dir=self.output_dir
            )
        except Exception as e:
            self.fail(f"Options initialization with valid options should not raise exception: {e}")


if __name__ == '__main__':
    unittest.main()