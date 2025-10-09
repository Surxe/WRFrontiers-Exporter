import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import from the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from mapper.get_mapper import find_existing_mapping_file


class TestFindExistingMappingFile(unittest.TestCase):
    """Test cases for find_existing_mapping_file function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.dumper7_output_dir = self.test_dir
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('mapper.get_mapper.get_mapper_from_sdk')
    def test_find_existing_mapping_file_success(self, mock_get_mapper):
        """Test find_existing_mapping_file when mapper is found successfully"""
        expected_path = "/path/to/mapper.usmap"
        mock_get_mapper.return_value = expected_path
        
        result = find_existing_mapping_file(self.dumper7_output_dir)
        
        self.assertEqual(result, expected_path)
        mock_get_mapper.assert_called_once_with(self.dumper7_output_dir)
    
    @patch('mapper.get_mapper.get_mapper_from_sdk')
    def test_find_existing_mapping_file_exception(self, mock_get_mapper):
        """Test find_existing_mapping_file when get_mapper_from_sdk raises exception"""
        mock_get_mapper.side_effect = Exception("SDK not found")
        
        result = find_existing_mapping_file(self.dumper7_output_dir)
        
        self.assertIsNone(result)
        mock_get_mapper.assert_called_once_with(self.dumper7_output_dir)
    
    @patch('mapper.get_mapper.get_mapper_from_sdk')
    def test_find_existing_mapping_file_returns_none_on_error(self, mock_get_mapper):
        """Test find_existing_mapping_file returns None when any exception occurs"""
        mock_get_mapper.side_effect = FileNotFoundError("File not found")
        
        result = find_existing_mapping_file(self.dumper7_output_dir)
        
        self.assertIsNone(result)
    
    @patch('mapper.get_mapper.get_mapper_from_sdk')
    def test_find_existing_mapping_file_with_empty_string_return(self, mock_get_mapper):
        """Test find_existing_mapping_file when get_mapper_from_sdk returns empty string"""
        mock_get_mapper.return_value = ""
        
        result = find_existing_mapping_file(self.dumper7_output_dir)
        
        self.assertEqual(result, "")
    
    @patch('mapper.get_mapper.get_mapper_from_sdk')
    def test_find_existing_mapping_file_with_none_return(self, mock_get_mapper):
        """Test find_existing_mapping_file when get_mapper_from_sdk returns None"""
        mock_get_mapper.return_value = None
        
        result = find_existing_mapping_file(self.dumper7_output_dir)
        
        self.assertIsNone(result)
    
    def test_find_existing_mapping_file_with_nonexistent_directory(self):
        """Test find_existing_mapping_file with non-existent directory"""
        nonexistent_dir = "/nonexistent/directory/path"
        
        result = find_existing_mapping_file(nonexistent_dir)
        
        # Should return None due to exception in get_mapper_from_sdk
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()