import unittest
import sys
import os

# Add the src directory to the Python path to import utils
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.utils module to avoid conflicts with tests.utils
import importlib.util
spec = importlib.util.spec_from_file_location("src_utils", os.path.join(src_path, "utils.py"))
src_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_utils)

normalize_path = src_utils.normalize_path


class TestNormalizePath(unittest.TestCase):
    """Test cases for the normalize_path function.
    
    The normalize_path function normalizes file paths to use forward slashes
    for cross-platform consistency while preserving absolute path characteristics.
    """

    def test_windows_absolute_path(self):
        """Test normalize_path handles Windows absolute paths."""
        input_path = "C:\\Users\\Test\\Documents\\file.txt"
        expected = "C:/Users/Test/Documents/file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_unix_absolute_path(self):
        """Test normalize_path handles Unix absolute paths."""
        input_path = "/home/user/documents/file.txt"
        expected = "/home/user/documents/file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_relative_path_with_backslashes(self):
        """Test normalize_path handles relative paths with backslashes."""
        input_path = "folder\\subfolder\\file.txt"
        expected = "folder/subfolder/file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_relative_path_with_forward_slashes(self):
        """Test normalize_path handles relative paths with forward slashes."""
        input_path = "folder/subfolder/file.txt"
        expected = "folder/subfolder/file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_mixed_slashes(self):
        """Test normalize_path handles mixed slash types."""
        input_path = "C:\\folder/subfolder\\file.txt"
        expected = "C:/folder/subfolder/file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_double_slashes(self):
        """Test normalize_path handles double slashes."""
        input_path = "folder\\\\subfolder//file.txt"
        # os.path.normpath should handle double slashes
        result = normalize_path(input_path)
        # The exact result depends on os.path.normpath behavior
        self.assertIn("folder", result)
        self.assertIn("subfolder", result)
        self.assertIn("file.txt", result)
        self.assertNotIn("\\", result)

    def test_current_directory_reference(self):
        """Test normalize_path handles current directory references."""
        input_path = ".\\folder\\file.txt"
        result = normalize_path(input_path)
        self.assertNotIn("\\", result)
        self.assertIn("folder", result)
        self.assertIn("file.txt", result)

    def test_parent_directory_reference(self):
        """Test normalize_path handles parent directory references."""
        input_path = "..\\folder\\file.txt"
        result = normalize_path(input_path)
        self.assertNotIn("\\", result)
        self.assertIn("..", result)
        self.assertIn("folder", result)

    def test_empty_string(self):
        """Test normalize_path handles empty string."""
        input_path = ""
        expected = "."  # os.path.normpath("") returns "."
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_single_filename(self):
        """Test normalize_path handles single filename."""
        input_path = "file.txt"
        expected = "file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_trailing_slash(self):
        """Test normalize_path handles trailing slashes."""
        input_path = "folder\\subfolder\\"
        result = normalize_path(input_path)
        self.assertNotIn("\\", result)
        # Behavior may vary based on os.path.normpath implementation

    def test_unc_path_windows(self):
        """Test normalize_path handles UNC paths on Windows."""
        input_path = "\\\\server\\share\\folder\\file.txt"
        result = normalize_path(input_path)
        self.assertNotIn("\\", result)
        # Should preserve the network path structure but with forward slashes

    def test_path_with_spaces(self):
        """Test normalize_path handles paths with spaces."""
        input_path = "C:\\Program Files\\My App\\file.txt"
        expected = "C:/Program Files/My App/file.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_path_with_unicode(self):
        """Test normalize_path handles paths with unicode characters."""
        input_path = "C:\\Users\\José\\Documents\\café.txt"
        expected = "C:/Users/José/Documents/café.txt"
        result = normalize_path(input_path)
        self.assertEqual(result, expected)

    def test_very_long_path(self):
        """Test normalize_path handles very long paths."""
        long_folder = "very_long_folder_name_" * 20
        input_path = f"C:\\{long_folder}\\file.txt"
        result = normalize_path(input_path)
        self.assertNotIn("\\", result)
        self.assertIn(long_folder, result)
        self.assertIn("file.txt", result)


if __name__ == '__main__':
    unittest.main()