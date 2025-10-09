import unittest
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the src directory to the Python path to import dependency_manager
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.dependency_manager module to avoid conflicts
import importlib.util
spec = importlib.util.spec_from_file_location("src_dependency_manager", os.path.join(src_path, "dependency_manager.py"))
src_dependency_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_dependency_manager)

DependencyManager = src_dependency_manager.DependencyManager


class TestValidateZipFile(unittest.TestCase):
    """Test cases for _validate_zip_file function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dm = DependencyManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test directory
        import shutil
        if self.test_path.exists():
            shutil.rmtree(self.test_path)

    def _create_valid_zip(self, zip_path, files=None):
        """Helper method to create a valid ZIP file for testing."""
        if files is None:
            # Create files with more content to ensure ZIP is over 1000 bytes
            files = {
                'test.txt': 'Test content ' * 200,  # Make content much larger
                'folder/file.txt': 'More content ' * 200,
                'data.bin': 'x' * 2000,  # Large binary-like content
                'padding.txt': 'P' * 1000  # Additional padding
            }
        else:
            # Ensure provided files create a large enough ZIP by adding padding
            files = dict(files)  # Copy to avoid modifying original
            files['_padding_'] = 'P' * 1500  # Always add padding
        
        # Use no compression to ensure file size is predictable and large
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)

    def test_validate_zip_file_valid_zip(self):
        """Test _validate_zip_file with a valid ZIP file."""
        zip_path = self.test_path / "test.zip"
        self._create_valid_zip(zip_path)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertTrue(result)
            # Check debug logging calls
            mock_logger.debug.assert_called()
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            self.assertTrue(any("Validating ZIP file" in call for call in debug_calls))
            # Files + padding files = more than 2
            self.assertTrue(any("ZIP contains" in call for call in debug_calls))

    def test_validate_zip_file_empty_zip(self):
        """Test _validate_zip_file with an empty ZIP file."""
        zip_path = self.test_path / "empty.zip"
        
        # Create ZIP with minimal content to ensure it's over 1000 bytes but logically "empty"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
            zf.writestr(".placeholder", "x" * 1200)  # Add minimal file to ensure size
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertTrue(result)  # ZIP should be valid
            mock_logger.debug.assert_called()
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            self.assertTrue(any("ZIP contains 1 files" in call for call in debug_calls))

    def test_validate_zip_file_invalid_zip(self):
        """Test _validate_zip_file with an invalid ZIP file (not a ZIP)."""
        zip_path = self.test_path / "invalid.zip"
        # Create content that's large enough but not a valid ZIP
        invalid_content = "This is not a ZIP file. " * 50  # Over 1000 bytes
        zip_path.write_text(invalid_content)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertFalse(result)
            mock_logger.error.assert_called_with("File is not a valid ZIP archive")

    def test_validate_zip_file_corrupted_zip(self):
        """Test _validate_zip_file with a corrupted ZIP file."""
        zip_path = self.test_path / "corrupted.zip"
        
        # Create a valid ZIP first, then corrupt it
        self._create_valid_zip(zip_path)
        
        # Corrupt the ZIP by truncating it but keep it above 1000 bytes
        original_size = zip_path.stat().st_size
        new_size = max(1001, original_size // 2)  # Keep above threshold but corrupt structure
        
        with open(zip_path, 'r+b') as f:
            f.seek(new_size)
            f.truncate()
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertFalse(result)
            mock_logger.error.assert_called_with("File is not a valid ZIP archive")

    def test_validate_zip_file_too_small(self):
        """Test _validate_zip_file with a file that's too small (likely error page)."""
        zip_path = self.test_path / "tiny.zip"
        zip_path.write_text("small")  # Only 5 bytes, less than 1000 byte threshold
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertFalse(result)
            mock_logger.error.assert_called_with("File is too small (5 bytes), likely an error page")

    def test_validate_zip_file_exactly_threshold_size(self):
        """Test _validate_zip_file with a file exactly at the size threshold."""
        zip_path = self.test_path / "threshold.zip"
        
        # Create content that results in more than 1000 bytes
        large_content = "x" * 2000  # Ensure ZIP will be over threshold
        self._create_valid_zip(zip_path, {'large.txt': large_content})
        
        # Verify the file is large enough
        file_size = zip_path.stat().st_size
        self.assertGreaterEqual(file_size, 1000)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertTrue(result)
            # Should not trigger "too small" error
            error_calls = [call for call in mock_logger.error.call_args_list if call]
            too_small_errors = [call for call in error_calls if "too small" in str(call)]
            self.assertEqual(len(too_small_errors), 0)

    def test_validate_zip_file_stat_exception(self):
        """Test _validate_zip_file handles file stat exceptions."""
        zip_path = self.test_path / "nonexistent.zip"
        # Don't create the file - stat() will fail
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertFalse(result)
            mock_logger.error.assert_called()
            error_message = mock_logger.error.call_args[0][0]
            self.assertIn("Error validating ZIP file", error_message)

    @patch('zipfile.ZipFile')
    def test_validate_zip_file_zipfile_exception(self, mock_zipfile):
        """Test _validate_zip_file handles ZipFile exceptions other than BadZipFile."""
        zip_path = self.test_path / "test.zip"
        zip_path.write_text("x" * 2000)  # Large enough to pass size check
        
        # Mock ZipFile to raise a generic exception
        mock_zipfile.side_effect = IOError("Disk full")
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertFalse(result)
            mock_logger.error.assert_called()
            error_message = mock_logger.error.call_args[0][0]
            self.assertIn("Error validating ZIP file: Disk full", error_message)

    def test_validate_zip_file_with_many_files(self):
        """Test _validate_zip_file with a ZIP containing many files."""
        zip_path = self.test_path / "many_files.zip"
        
        # Create ZIP with many files
        files = {f"file_{i}.txt": f"Content {i}" for i in range(50)}
        self._create_valid_zip(zip_path, files)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertTrue(result)
            mock_logger.debug.assert_called()
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            # Should contain 50 original files + 1 padding file = 51 total
            self.assertTrue(any("ZIP contains 51 files" in call for call in debug_calls))

    def test_validate_zip_file_logs_file_size(self):
        """Test that _validate_zip_file logs the file size correctly."""
        zip_path = self.test_path / "size_test.zip"
        self._create_valid_zip(zip_path)
        
        actual_size = zip_path.stat().st_size
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            result = self.dm._validate_zip_file(zip_path)
            
            self.assertTrue(result)
            # Check that size was logged correctly
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            size_log = next((call for call in debug_calls if "Validating ZIP file" in call), None)
            self.assertIsNotNone(size_log)
            self.assertIn(f"({actual_size} bytes)", size_log)

    @patch.object(src_dependency_manager, 'logger')
    def test_validate_zip_file_logs_debug_info(self, mock_logger):
        """Test that _validate_zip_file logs appropriate debug information."""
        zip_path = self.test_path / "debug_test.zip"
        files = {'readme.txt': 'Hello', 'data/info.json': '{"test": true}'}
        self._create_valid_zip(zip_path, files)
        
        result = self.dm._validate_zip_file(zip_path)
        
        self.assertTrue(result)
        
        # Verify debug logging calls
        self.assertGreaterEqual(mock_logger.debug.call_count, 2)
        debug_messages = [call[0][0] for call in mock_logger.debug.call_args_list]
        
        # Check for validation message
        validation_msg = next((msg for msg in debug_messages if "Validating ZIP file" in msg), None)
        self.assertIsNotNone(validation_msg)
        self.assertIn("debug_test.zip", validation_msg)
        
        # Check for file count message (2 original files + 1 padding = 3)
        count_msg = next((msg for msg in debug_messages if "ZIP contains" in msg), None)
        self.assertIsNotNone(count_msg)
        self.assertIn("3 files", count_msg)


if __name__ == '__main__':
    unittest.main()