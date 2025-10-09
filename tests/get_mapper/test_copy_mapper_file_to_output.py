import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import from the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from mapper.get_mapper import copy_mapper_file_to_output


class TestCopyMapperFileToOutput(unittest.TestCase):
    """Test cases for copy_mapper_file_to_output function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.source_file = os.path.join(self.test_dir, "source_mapper.usmap")
        self.output_file = os.path.join(self.test_dir, "output", "mapper.usmap")
        
        # Create source file with test content
        with open(self.source_file, 'w') as f:
            f.write("test mapper content")
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_copy_mapper_file_success(self):
        """Test successful copying of mapper file"""
        result = copy_mapper_file_to_output(self.source_file, self.output_file)
        
        self.assertEqual(result, self.output_file)
        self.assertTrue(os.path.exists(self.output_file))
        
        # Verify content was copied correctly
        with open(self.output_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "test mapper content")
    
    def test_copy_mapper_file_creates_parent_directory(self):
        """Test that copy_mapper_file_to_output creates parent directories"""
        nested_output = os.path.join(self.test_dir, "deep", "nested", "path", "mapper.usmap")
        
        result = copy_mapper_file_to_output(self.source_file, nested_output)
        
        self.assertEqual(result, nested_output)
        self.assertTrue(os.path.exists(nested_output))
        self.assertTrue(os.path.exists(os.path.dirname(nested_output)))
    
    def test_copy_mapper_file_source_not_exists(self):
        """Test copy_mapper_file_to_output when source file does not exist"""
        nonexistent_source = os.path.join(self.test_dir, "nonexistent.usmap")
        
        result = copy_mapper_file_to_output(nonexistent_source, self.output_file)
        
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(self.output_file))
    
    @patch('mapper.get_mapper.logger')
    def test_copy_mapper_file_logs_error_on_missing_source(self, mock_logger):
        """Test that error is logged when source file is missing"""
        nonexistent_source = os.path.join(self.test_dir, "nonexistent.usmap")
        
        result = copy_mapper_file_to_output(nonexistent_source, self.output_file)
        
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Source mapper file does not exist", error_msg)
    
    @patch('mapper.get_mapper.logger')
    def test_copy_mapper_file_logs_success(self, mock_logger):
        """Test that success is logged when file is copied"""
        result = copy_mapper_file_to_output(self.source_file, self.output_file)
        
        self.assertEqual(result, self.output_file)
        mock_logger.info.assert_called_once()
        info_msg = mock_logger.info.call_args[0][0]
        self.assertIn("Mapper file copied from", info_msg)
        self.assertIn(self.source_file, info_msg)
        self.assertIn(self.output_file, info_msg)
    
    @patch('shutil.copy2')
    @patch('mapper.get_mapper.logger')
    def test_copy_mapper_file_handles_copy_exception(self, mock_logger, mock_copy):
        """Test copy_mapper_file_to_output handles shutil.copy2 exceptions"""
        mock_copy.side_effect = PermissionError("Permission denied")
        
        result = copy_mapper_file_to_output(self.source_file, self.output_file)
        
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to copy mapper file", error_msg)
    
    def test_copy_mapper_file_overwrites_existing(self):
        """Test that copy_mapper_file_to_output overwrites existing files"""
        # Create output directory and file with different content
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w') as f:
            f.write("old content")
        
        result = copy_mapper_file_to_output(self.source_file, self.output_file)
        
        self.assertEqual(result, self.output_file)
        
        # Verify content was overwritten
        with open(self.output_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "test mapper content")
    
    @patch('os.makedirs')
    @patch('mapper.get_mapper.logger')
    def test_copy_mapper_file_handles_makedirs_exception(self, mock_logger, mock_makedirs):
        """Test copy_mapper_file_to_output handles os.makedirs exceptions"""
        mock_makedirs.side_effect = PermissionError("Cannot create directory")
        
        result = copy_mapper_file_to_output(self.source_file, self.output_file)
        
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()