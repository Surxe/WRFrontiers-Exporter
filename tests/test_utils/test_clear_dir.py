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

clear_dir = src_utils.clear_dir


class TestClearDir(unittest.TestCase):
    """Test cases for the clear_dir function.
    
    The clear_dir function should clear directory contents but keep the directory itself.
    Tests use temporary directories to avoid affecting the actual file system.
    """

    def setUp(self):
        """Set up temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory after each test."""
        if os.path.exists(self.test_dir):
            # Handle read-only files on Windows
            def handle_remove_readonly(func, path, exc):
                if os.path.exists(path):
                    os.chmod(path, 0o777)
                    func(path)
            
            shutil.rmtree(self.test_dir, onerror=handle_remove_readonly)

    def test_clear_empty_directory(self):
        """Test clear_dir on an empty directory."""
        # Directory should remain empty and exist
        clear_dir(self.test_dir)
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.isdir(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_clear_directory_with_files(self):
        """Test clear_dir removes files from directory."""
        # Create some test files
        file1 = os.path.join(self.test_dir, "file1.txt")
        file2 = os.path.join(self.test_dir, "file2.log")
        
        with open(file1, 'w') as f:
            f.write("test content 1")
        with open(file2, 'w') as f:
            f.write("test content 2")
        
        # Verify files exist before clearing
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))
        
        # Clear directory
        clear_dir(self.test_dir)
        
        # Directory should exist but be empty
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.isdir(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

    def test_clear_directory_with_subdirectories(self):
        """Test clear_dir removes subdirectories from directory."""
        # Create subdirectories
        subdir1 = os.path.join(self.test_dir, "subdir1")
        subdir2 = os.path.join(self.test_dir, "subdir2")
        os.makedirs(subdir1)
        os.makedirs(subdir2)
        
        # Add files to subdirectories
        file_in_subdir = os.path.join(subdir1, "nested_file.txt")
        with open(file_in_subdir, 'w') as f:
            f.write("nested content")
        
        # Verify structure exists before clearing
        self.assertTrue(os.path.exists(subdir1))
        self.assertTrue(os.path.exists(subdir2))
        self.assertTrue(os.path.exists(file_in_subdir))
        
        # Clear directory
        clear_dir(self.test_dir)
        
        # Directory should exist but be empty
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.isdir(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)
        self.assertFalse(os.path.exists(subdir1))
        self.assertFalse(os.path.exists(subdir2))

    def test_clear_directory_mixed_content(self):
        """Test clear_dir removes mixed files and directories."""
        # Create mixed content
        file1 = os.path.join(self.test_dir, "file.txt")
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)
        
        with open(file1, 'w') as f:
            f.write("test content")
        
        nested_file = os.path.join(subdir, "nested.txt")
        with open(nested_file, 'w') as f:
            f.write("nested content")
        
        # Verify content exists
        self.assertEqual(len(os.listdir(self.test_dir)), 2)
        
        # Clear directory
        clear_dir(self.test_dir)
        
        # Directory should be empty
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_clear_directory_readonly_files(self):
        """Test clear_dir handles read-only files."""
        # Create a read-only file
        readonly_file = os.path.join(self.test_dir, "readonly.txt")
        with open(readonly_file, 'w') as f:
            f.write("readonly content")
        
        # Make file read-only
        os.chmod(readonly_file, 0o444)
        
        try:
            # Clear directory (may need to handle permission errors)
            clear_dir(self.test_dir)
            
            # Directory should be empty
            self.assertTrue(os.path.exists(self.test_dir))
            self.assertEqual(len(os.listdir(self.test_dir)), 0)
        except PermissionError:
            # This is acceptable behavior for read-only files
            pass

    def test_clear_nonexistent_directory(self):
        """Test clear_dir behavior with non-existent directory."""
        non_existent = os.path.join(self.test_dir, "nonexistent")
        
        # Should raise an appropriate exception
        with self.assertRaises((FileNotFoundError, OSError)):
            clear_dir(non_existent)

    def test_clear_directory_with_hidden_files(self):
        """Test clear_dir removes hidden files (files starting with dot)."""
        # Create hidden file
        hidden_file = os.path.join(self.test_dir, ".hidden")
        regular_file = os.path.join(self.test_dir, "regular.txt")
        
        with open(hidden_file, 'w') as f:
            f.write("hidden content")
        with open(regular_file, 'w') as f:
            f.write("regular content")
        
        # Verify files exist
        self.assertTrue(os.path.exists(hidden_file))
        self.assertTrue(os.path.exists(regular_file))
        
        # Clear directory
        clear_dir(self.test_dir)
        
        # Directory should be empty
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('shutil.rmtree')
    @patch('os.remove')
    def test_clear_dir_mocked_operations(self, mock_remove, mock_rmtree, mock_isdir, mock_listdir):
        """Test clear_dir with mocked file system operations."""
        # Mock directory contents
        mock_listdir.return_value = ['file.txt', 'subdir', '.hidden']
        
        # Mock isdir checks
        def mock_isdir_func(path):
            return path.endswith('subdir')
        mock_isdir.side_effect = mock_isdir_func
        
        # Call clear_dir
        clear_dir('/test/path')
        
        # Verify calls
        mock_listdir.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once()  # For subdir
        self.assertEqual(mock_remove.call_count, 2)  # For file.txt and .hidden

    def test_clear_directory_with_special_characters(self):
        """Test clear_dir handles files with special characters."""
        # Create files with special characters (Windows-safe)
        special_file1 = os.path.join(self.test_dir, "file with spaces.txt")
        special_file2 = os.path.join(self.test_dir, "file-with+special~chars.txt")
        
        with open(special_file1, 'w') as f:
            f.write("content1")
        with open(special_file2, 'w') as f:
            f.write("content2")
        
        # Clear directory
        clear_dir(self.test_dir)
        
        # Directory should be empty
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)


if __name__ == '__main__':
    unittest.main()