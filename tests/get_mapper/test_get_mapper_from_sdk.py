import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import from the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from mapper.get_mapper import get_mapper_from_sdk


class TestGetMapperFromSdk(unittest.TestCase):
    """Test cases for get_mapper_from_sdk function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.dumper7_output_dir = self.test_dir
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_valid_sdk_structure(self):
        """Helper method to create a valid SDK directory structure"""
        sdk_dir = os.path.join(self.dumper7_output_dir, "TestSDK")
        mappings_dir = os.path.join(sdk_dir, "Mappings")
        os.makedirs(mappings_dir)
        
        mapper_file = os.path.join(mappings_dir, "test_mapper.usmap")
        with open(mapper_file, 'w') as f:
            f.write("test mapper content")
        
        return mapper_file
    
    def test_get_mapper_from_sdk_success(self):
        """Test get_mapper_from_sdk with valid SDK structure"""
        expected_mapper_file = self.create_valid_sdk_structure()
        
        result = get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertEqual(result, expected_mapper_file)
        self.assertTrue(os.path.exists(result))
    
    def test_get_mapper_from_sdk_no_directories(self):
        """Test get_mapper_from_sdk when no directories exist in output path"""
        # Empty directory - no subdirectories
        
        with self.assertRaises(Exception) as context:
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertIn("Invalid SDK directory structure", str(context.exception))
        self.assertIn("found 0 directories instead of 1", str(context.exception))
    
    def test_get_mapper_from_sdk_multiple_directories(self):
        """Test get_mapper_from_sdk when multiple directories exist"""
        # Create multiple SDK directories
        os.makedirs(os.path.join(self.dumper7_output_dir, "SDK1"))
        os.makedirs(os.path.join(self.dumper7_output_dir, "SDK2"))
        
        with self.assertRaises(Exception) as context:
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertIn("Invalid SDK directory structure", str(context.exception))
        self.assertIn("found 2 directories instead of 1", str(context.exception))
    
    def test_get_mapper_from_sdk_no_mappings_directory(self):
        """Test get_mapper_from_sdk when Mappings directory does not exist"""
        # Create SDK directory without Mappings subdirectory
        sdk_dir = os.path.join(self.dumper7_output_dir, "TestSDK")
        os.makedirs(sdk_dir)
        
        with self.assertRaises(Exception) as context:
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertIn("Mappings directory not found", str(context.exception))
    
    def test_get_mapper_from_sdk_no_mapper_files(self):
        """Test get_mapper_from_sdk when Mappings directory is empty"""
        # Create SDK structure but no mapper files
        sdk_dir = os.path.join(self.dumper7_output_dir, "TestSDK")
        mappings_dir = os.path.join(sdk_dir, "Mappings")
        os.makedirs(mappings_dir)
        
        with self.assertRaises(Exception) as context:
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertIn("No mapper files found", str(context.exception))
    
    def test_get_mapper_from_sdk_multiple_mapper_files(self):
        """Test get_mapper_from_sdk when multiple mapper files exist"""
        # Create SDK structure with multiple mapper files
        sdk_dir = os.path.join(self.dumper7_output_dir, "TestSDK")
        mappings_dir = os.path.join(sdk_dir, "Mappings")
        os.makedirs(mappings_dir)
        
        # Create multiple mapper files
        with open(os.path.join(mappings_dir, "mapper1.usmap"), 'w') as f:
            f.write("mapper1")
        with open(os.path.join(mappings_dir, "mapper2.usmap"), 'w') as f:
            f.write("mapper2")
        
        with self.assertRaises(Exception) as context:
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertIn("Multiple mapper files found", str(context.exception))
        self.assertIn("expected only one", str(context.exception))
    
    def test_get_mapper_from_sdk_mapper_file_not_exists(self):
        """Test get_mapper_from_sdk when mapper file path doesn't actually exist"""
        # This is an edge case where listdir shows file but exists check fails
        sdk_dir = os.path.join(self.dumper7_output_dir, "TestSDK")
        mappings_dir = os.path.join(sdk_dir, "Mappings")
        os.makedirs(mappings_dir)
        
        mapper_file = os.path.join(mappings_dir, "test_mapper.usmap")
        with open(mapper_file, 'w') as f:
            f.write("test content")
        
        # Mock os.path.exists to return False for the specific mapper file
        with patch('os.path.exists') as mock_exists:
            def exists_side_effect(path):
                if path == mapper_file:
                    return False
                return True  # For other paths like directories
            
            mock_exists.side_effect = exists_side_effect
            
            with self.assertRaises(Exception) as context:
                get_mapper_from_sdk(self.dumper7_output_dir)
            
            self.assertIn("Mapper file not found", str(context.exception))
    
    @patch('mapper.get_mapper.logger')
    def test_get_mapper_from_sdk_logs_success(self, mock_logger):
        """Test that get_mapper_from_sdk logs success messages"""
        expected_mapper_file = self.create_valid_sdk_structure()
        
        result = get_mapper_from_sdk(self.dumper7_output_dir)
        
        # Should log SDK creation success and mapper file success
        self.assertEqual(mock_logger.info.call_count, 2)
        
        # Check for SDK success log
        sdk_log_found = False
        mapper_log_found = False
        for call in mock_logger.info.call_args_list:
            log_msg = call[0][0]
            if "SDK creation appears to have succeeded" in log_msg:
                sdk_log_found = True
            elif "Mapper file successfully created" in log_msg:
                mapper_log_found = True
        
        self.assertTrue(sdk_log_found, "SDK success log not found")
        self.assertTrue(mapper_log_found, "Mapper success log not found")
    
    @patch('mapper.get_mapper.logger')
    def test_get_mapper_from_sdk_logs_errors(self, mock_logger):
        """Test that get_mapper_from_sdk logs appropriate error messages"""
        # Test with no directories
        with self.assertRaises(Exception):
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Expected exactly one directory", error_msg)
    
    def test_get_mapper_from_sdk_ignores_files_in_root(self):
        """Test that get_mapper_from_sdk ignores files in the root directory"""
        # Create a file in the root directory
        with open(os.path.join(self.dumper7_output_dir, "somefile.txt"), 'w') as f:
            f.write("ignore me")
        
        # Should still fail because no directories exist
        with self.assertRaises(Exception) as context:
            get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertIn("found 0 directories instead of 1", str(context.exception))
    
    def test_get_mapper_from_sdk_with_subdirectories_in_mappings(self):
        """Test get_mapper_from_sdk when Mappings contains subdirectories"""
        # Create SDK structure
        sdk_dir = os.path.join(self.dumper7_output_dir, "TestSDK")
        mappings_dir = os.path.join(sdk_dir, "Mappings")
        os.makedirs(mappings_dir)
        
        # Create subdirectory in Mappings (should be ignored)
        os.makedirs(os.path.join(mappings_dir, "subdir"))
        
        # Create single mapper file
        mapper_file = os.path.join(mappings_dir, "test_mapper.usmap")
        with open(mapper_file, 'w') as f:
            f.write("test content")
        
        result = get_mapper_from_sdk(self.dumper7_output_dir)
        
        self.assertEqual(result, mapper_file)


if __name__ == '__main__':
    unittest.main()