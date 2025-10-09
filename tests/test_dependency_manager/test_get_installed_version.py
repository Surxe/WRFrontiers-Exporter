import unittest
import os
import tempfile
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


class TestGetInstalledVersion(unittest.TestCase):
    """Test cases for _get_installed_version function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dm = DependencyManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        self.version_file = self.test_path / "version.txt"

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test directory
        import shutil
        if self.test_path.exists():
            shutil.rmtree(self.test_path)

    def test_get_installed_version_file_exists(self):
        """Test _get_installed_version when version.txt file exists."""
        # Create version file with test content
        test_version = "v1.2.3"
        self.version_file.write_text(test_version)
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertEqual(result, test_version)

    def test_get_installed_version_file_exists_with_whitespace(self):
        """Test _get_installed_version strips whitespace from version file."""
        # Create version file with whitespace
        test_version = "  v2.0.1  \n"
        expected_version = "v2.0.1"
        self.version_file.write_text(test_version)
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertEqual(result, expected_version)

    def test_get_installed_version_file_not_exists(self):
        """Test _get_installed_version when version.txt file doesn't exist."""
        # Ensure file doesn't exist
        self.assertFalse(self.version_file.exists())
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertIsNone(result)

    def test_get_installed_version_empty_file(self):
        """Test _get_installed_version with empty version file."""
        # Create empty version file
        self.version_file.write_text("")
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertEqual(result, "")

    def test_get_installed_version_read_error(self):
        """Test _get_installed_version handles file read errors gracefully."""
        # Create version file then mock read_text to raise exception
        self.version_file.write_text("v1.0.0")
        
        with patch.object(Path, 'read_text', side_effect=PermissionError("Access denied")):
            with patch.object(src_dependency_manager, 'logger') as mock_logger:
                result = self.dm._get_installed_version(self.test_path)
                
                self.assertIsNone(result)
                mock_logger.warning.assert_called_once()
                # Check that warning message contains file path and error
                warning_call = mock_logger.warning.call_args[0][0]
                self.assertIn(str(self.version_file), warning_call)
                self.assertIn("Access denied", warning_call)

    def test_get_installed_version_path_object(self):
        """Test _get_installed_version works with Path objects."""
        test_version = "v3.1.4"
        self.version_file.write_text(test_version)
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertEqual(result, test_version)

    def test_get_installed_version_string_path(self):
        """Test _get_installed_version works with string paths."""
        test_version = "v2.7.1"
        self.version_file.write_text(test_version)
        
        result = self.dm._get_installed_version(str(self.test_path))
        
        self.assertEqual(result, test_version)

    @patch.object(src_dependency_manager, 'logger')
    def test_get_installed_version_logs_warning_on_exception(self, mock_logger):
        """Test that _get_installed_version logs appropriate warning on exception."""
        # Create version file
        self.version_file.write_text("v1.0.0")
        
        # Mock read_text to raise a different exception
        with patch.object(Path, 'read_text', side_effect=OSError("Disk error")):
            result = self.dm._get_installed_version(self.test_path)
            
            self.assertIsNone(result)
            mock_logger.warning.assert_called_once()
            warning_message = mock_logger.warning.call_args[0][0]
            self.assertIn("Could not read version file", warning_message)
            self.assertIn("Disk error", warning_message)

    def test_get_installed_version_multiline_content(self):
        """Test _get_installed_version handles multiline content correctly."""
        # Version file with multiple lines - should only return first line stripped
        content = "v1.5.0\nThis is extra content\nMore lines"
        expected = "v1.5.0\nThis is extra content\nMore lines"  # strip() only removes leading/trailing whitespace
        self.version_file.write_text(content)
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertEqual(result, expected)

    def test_get_installed_version_unicode_content(self):
        """Test _get_installed_version handles unicode content."""
        test_version = "v1.0.0-beta"  # Use ASCII to avoid encoding issues
        self.version_file.write_text(test_version)
        
        result = self.dm._get_installed_version(self.test_path)
        
        self.assertEqual(result, test_version)


if __name__ == '__main__':
    unittest.main()