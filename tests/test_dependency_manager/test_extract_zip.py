import unittest
import os
import tempfile
import zipfile
import shutil
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


class TestExtractZip(unittest.TestCase):
    """Test cases for _extract_zip function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dm = DependencyManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        self.zip_path = self.test_path / "test.zip"
        self.output_path = self.test_path / "output"
        self.output_path.mkdir()

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test directory
        if self.test_path.exists():
            shutil.rmtree(self.test_path)

    def _create_test_zip(self, zip_path, files=None, use_subdirectory=False):
        """Helper method to create a test ZIP file."""
        if files is None:
            files = {'readme.txt': 'Hello World', 'data/config.json': '{"test": true}'}
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                if use_subdirectory:
                    filename = f"subdir/{filename}"
                zf.writestr(filename, content)

    def test_extract_zip_basic_extraction(self):
        """Test basic ZIP extraction functionality."""
        files = {'readme.txt': 'Hello World', 'config.json': '{"version": "1.0"}'}
        self._create_test_zip(self.zip_path, files)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Verify files were extracted
            self.assertTrue((self.output_path / 'readme.txt').exists())
            self.assertTrue((self.output_path / 'config.json').exists())
            
            # Verify file contents
            self.assertEqual((self.output_path / 'readme.txt').read_text(), 'Hello World')
            self.assertEqual((self.output_path / 'config.json').read_text(), '{"version": "1.0"}')
            
            # Check logging
            mock_logger.info.assert_called_with("Extracted 2 files to " + str(self.output_path))

    def test_extract_zip_with_subdirectories(self):
        """Test ZIP extraction with subdirectories."""
        files = {
            'readme.txt': 'Root file',
            'docs/manual.txt': 'Documentation',
            'src/main.py': 'print("hello")',
            'src/utils/helper.py': 'def help(): pass'
        }
        self._create_test_zip(self.zip_path, files)
        
        with patch.object(src_dependency_manager, 'logger'):
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Verify directory structure was preserved
            self.assertTrue((self.output_path / 'readme.txt').exists())
            self.assertTrue((self.output_path / 'docs').is_dir())
            self.assertTrue((self.output_path / 'docs' / 'manual.txt').exists())
            self.assertTrue((self.output_path / 'src').is_dir())
            self.assertTrue((self.output_path / 'src' / 'main.py').exists())
            self.assertTrue((self.output_path / 'src' / 'utils').is_dir())
            self.assertTrue((self.output_path / 'src' / 'utils' / 'helper.py').exists())

    def test_extract_zip_flattens_single_subdirectory(self):
        """Test that extraction flattens structure when everything is in single subdirectory."""
        # Create ZIP where all files are in a single subdirectory (proper structure for flattening)
        files = {'file1.txt': 'Content 1', 'file2.txt': 'Content 2', 'nested/file3.txt': 'Content 3'}
        self._create_test_zip(self.zip_path, files, use_subdirectory=True)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Files should be moved to root level (flattened from the main subdir)
            self.assertTrue((self.output_path / 'file1.txt').exists())
            self.assertTrue((self.output_path / 'file2.txt').exists())
            self.assertTrue((self.output_path / 'nested' / 'file3.txt').exists())
            
            # Should have been flattened - main subdir should be removed

    def test_extract_zip_logs_archive_contents(self):
        """Test that _extract_zip logs the archive contents."""
        files = {f'file_{i}.txt': f'Content {i}' for i in range(5)}
        self._create_test_zip(self.zip_path, files)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Check debug logging for archive contents
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            self.assertTrue(any("Archive contents:" in call for call in debug_calls))
            
            # Should log individual files
            for i in range(5):
                filename = f'file_{i}.txt'
                self.assertTrue(any(filename in call for call in debug_calls))

    def test_extract_zip_logs_many_files_truncated(self):
        """Test that _extract_zip truncates file list logging for many files."""
        # Create ZIP with more than 10 files
        files = {f'file_{i:03d}.txt': f'Content {i}' for i in range(15)}
        self._create_test_zip(self.zip_path, files)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Check that logging was truncated
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            truncation_msg = next((call for call in debug_calls if "... and" in call and "more files" in call), None)
            self.assertIsNotNone(truncation_msg)
            self.assertIn("... and 5 more files", truncation_msg)

    def test_extract_zip_empty_archive(self):
        """Test extraction of an empty ZIP archive."""
        self._create_test_zip(self.zip_path, {})  # Empty ZIP
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Should complete without error
            mock_logger.info.assert_called_with("Extracted 0 files to " + str(self.output_path))

    def test_extract_zip_handles_zipfile_exception(self):
        """Test that _extract_zip handles ZipFile exceptions properly."""
        # Create an invalid ZIP file
        self.zip_path.write_text("Not a real ZIP file")
        
        with self.assertRaises(Exception) as context:
            self.dm._extract_zip(self.zip_path, self.output_path)
        
        self.assertIn("Failed to extract ZIP file", str(context.exception))

    @patch('zipfile.ZipFile')
    def test_extract_zip_handles_extraction_error(self, mock_zipfile_class):
        """Test _extract_zip handles errors during extraction process."""
        # Mock ZipFile to raise exception during extractall
        mock_zipfile = MagicMock()
        mock_zipfile.__enter__ = MagicMock(return_value=mock_zipfile)
        mock_zipfile.__exit__ = MagicMock(return_value=None)
        mock_zipfile.namelist.return_value = ['file1.txt', 'file2.txt']
        mock_zipfile.extractall.side_effect = PermissionError("Access denied")
        mock_zipfile_class.return_value = mock_zipfile
        
        with self.assertRaises(Exception) as context:
            self.dm._extract_zip(self.zip_path, self.output_path)
        
        self.assertIn("Failed to extract ZIP file: Access denied", str(context.exception))

    def test_extract_zip_calls_flatten_extraction(self):
        """Test that _extract_zip calls _flatten_extraction."""
        files = {'test.txt': 'content'}
        self._create_test_zip(self.zip_path, files)
        
        with patch.object(self.dm, '_flatten_extraction') as mock_flatten:
            with patch.object(src_dependency_manager, 'logger'):
                self.dm._extract_zip(self.zip_path, self.output_path)
                
                mock_flatten.assert_called_once_with(self.output_path)

    def test_extract_zip_large_file_count_logging(self):
        """Test logging behavior with exactly 10 files (boundary condition)."""
        files = {f'file_{i:02d}.txt': f'Content {i}' for i in range(10)}
        self._create_test_zip(self.zip_path, files)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Should log all 10 files without truncation
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            truncation_msg = next((call for call in debug_calls if "... and" in call and "more files" in call), None)
            self.assertIsNone(truncation_msg)  # Should not truncate with exactly 10 files

    def test_extract_zip_preserves_file_permissions(self):
        """Test that file extraction preserves basic file structure."""
        files = {
            'executable.exe': b'\x4d\x5a\x90\x00',  # Binary content (mock PE header)
            'script.sh': '#!/bin/bash\necho "hello"',
            'data.txt': 'Plain text content'
        }
        
        with zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                if isinstance(content, bytes):
                    zf.writestr(filename, content)
                else:
                    zf.writestr(filename, content.encode('utf-8'))
        
        with patch.object(src_dependency_manager, 'logger'):
            self.dm._extract_zip(self.zip_path, self.output_path)
            
            # Verify all files exist
            self.assertTrue((self.output_path / 'executable.exe').exists())
            self.assertTrue((self.output_path / 'script.sh').exists())
            self.assertTrue((self.output_path / 'data.txt').exists())
            
            # Verify text file content
            self.assertEqual((self.output_path / 'data.txt').read_text(), 'Plain text content')

    @patch.object(src_dependency_manager, 'logger')
    def test_extract_zip_logs_extraction_summary(self, mock_logger):
        """Test that _extract_zip logs extraction summary with file count and path."""
        files = {'file1.txt': 'content1', 'file2.txt': 'content2', 'dir/file3.txt': 'content3'}
        self._create_test_zip(self.zip_path, files)
        
        self.dm._extract_zip(self.zip_path, self.output_path)
        
        # Verify info logging with correct file count and path
        mock_logger.info.assert_called_with(f"Extracted 3 files to {self.output_path}")
        
        # Verify debug logging for archive contents
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        self.assertTrue(any("Archive contents:" in call for call in debug_calls))


if __name__ == '__main__':
    unittest.main()