import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import from the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from mapper.get_mapper import get_dll_path


class TestGetDllPath(unittest.TestCase):
    """Test cases for get_dll_path function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.original_cwd = os.getcwd()
    
    def tearDown(self):
        """Clean up after each test method."""
        os.chdir(self.original_cwd)
    
    @patch('os.path.exists')
    def test_get_dll_path_exists(self, mock_exists):
        """Test get_dll_path when DLL file exists"""
        mock_exists.return_value = True
        
        dll_path = get_dll_path()
        
        # Should return the expected path
        expected_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'mapper', 'Dumper-7.dll')
        expected_path = expected_path.replace('tests', 'src')
        self.assertTrue(dll_path.endswith('Dumper-7.dll'))
        mock_exists.assert_called_once()
    
    @patch('os.path.exists')
    def test_get_dll_path_not_exists(self, mock_exists):
        """Test get_dll_path when DLL file does not exist"""
        mock_exists.return_value = False
        
        with self.assertRaises(Exception) as context:
            get_dll_path()
        
        self.assertIn("DLL file not found", str(context.exception))
        mock_exists.assert_called_once()
    
    @patch('os.path.exists')
    @patch('mapper.get_mapper.logger')
    def test_get_dll_path_logs_confirmation(self, mock_logger, mock_exists):
        """Test that get_dll_path logs DLL confirmation when file exists"""
        mock_exists.return_value = True
        
        dll_path = get_dll_path()
        
        # Should log the DLL confirmation
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        self.assertIn("DLL file confirmed", log_call_args)
        self.assertIn(dll_path, log_call_args)
    
    def test_get_dll_path_returns_absolute_path(self):
        """Test that get_dll_path returns an absolute path"""
        with patch('os.path.exists', return_value=True):
            dll_path = get_dll_path()
            self.assertTrue(os.path.isabs(dll_path))
    
    def test_get_dll_path_correct_filename(self):
        """Test that get_dll_path returns path ending with correct DLL name"""
        with patch('os.path.exists', return_value=True):
            dll_path = get_dll_path()
            self.assertTrue(dll_path.endswith('Dumper-7.dll'))


if __name__ == '__main__':
    unittest.main()