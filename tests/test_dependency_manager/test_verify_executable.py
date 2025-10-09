import unittest
import os
import tempfile
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


class TestVerifyExecutable(unittest.TestCase):
    """Test cases for _verify_executable function"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dm = DependencyManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        self.output_path = self.test_path / "output"
        self.output_path.mkdir()

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test directory
        if self.test_path.exists():
            shutil.rmtree(self.test_path)

    def _create_test_executable(self, path, content="Mock executable content", size_bytes=None):
        """Helper method to create a test executable file."""
        if size_bytes:
            content = "x" * size_bytes
        path.write_text(content)
        
        # Make executable on Unix-like systems if os.chmod is available
        if hasattr(os, 'chmod'):
            path.chmod(0o755)

    def test_verify_executable_exists_in_root(self):
        """Test _verify_executable when executable exists in the root directory."""
        executable_name = "test.exe"
        executable_path = self.output_path / executable_name
        self._create_test_executable(executable_path, size_bytes=1024)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            # Should complete without exception
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Verify logging
            mock_logger.info.assert_called()
            info_message = mock_logger.info.call_args[0][0]
            self.assertIn(f"Verified executable: {executable_path} (1024 bytes)", info_message)

    def test_verify_executable_not_exists_raises_exception(self):
        """Test _verify_executable raises exception when executable doesn't exist."""
        executable_name = "nonexistent.exe"
        
        with self.assertRaises(Exception) as context:
            self.dm._verify_executable(self.output_path, executable_name)
        
        self.assertEqual(str(context.exception), f"Executable {executable_name} not found after extraction")

    def test_verify_executable_found_in_subdirectory(self):
        """Test _verify_executable finds and moves executable from subdirectory."""
        executable_name = "app.exe"
        
        # Create executable in subdirectory
        subdir = self.output_path / "bin"
        subdir.mkdir()
        executable_subpath = subdir / executable_name
        self._create_test_executable(executable_subpath, size_bytes=2048)
        
        expected_root_path = self.output_path / executable_name
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Verify executable was moved to root
            self.assertTrue(expected_root_path.exists())
            self.assertFalse(executable_subpath.exists())
            
            # Verify logging for move operation
            move_log_found = False
            for call in mock_logger.info.call_args_list:
                message = call[0][0]
                if "Moved executable from" in message and "to root" in message:
                    move_log_found = True
                    # Use os.sep or check for both separators since paths can vary by OS
                    self.assertTrue(f"bin{os.sep}{executable_name}" in message or f"bin/{executable_name}" in message)
                    break
            self.assertTrue(move_log_found, "Move operation was not logged properly")

    def test_verify_executable_found_in_nested_subdirectory(self):
        """Test _verify_executable finds executable in deeply nested subdirectory."""
        executable_name = "deep.exe"
        
        # Create nested directory structure
        deep_dir = self.output_path / "level1" / "level2" / "bin"
        deep_dir.mkdir(parents=True)
        executable_path = deep_dir / executable_name
        self._create_test_executable(executable_path)
        
        expected_root_path = self.output_path / executable_name
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Verify executable was moved to root
            self.assertTrue(expected_root_path.exists())
            self.assertFalse(executable_path.exists())
            
            # Check move logging (handle OS path separators)
            move_messages = [call[0][0] for call in mock_logger.info.call_args_list if "Moved executable" in call[0][0]]
            self.assertTrue(len(move_messages) > 0)
            expected_path = os.path.join("level1", "level2", "bin", "deep.exe")
            self.assertIn(expected_path, move_messages[0])

    def test_verify_executable_multiple_matches_uses_first(self):
        """Test _verify_executable uses first match when multiple executables with same name exist."""
        executable_name = "common.exe"
        
        # Create multiple executables with same name in different locations
        dir1 = self.output_path / "dir1"
        dir2 = self.output_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        exec1_path = dir1 / executable_name
        exec2_path = dir2 / executable_name
        self._create_test_executable(exec1_path, "First executable")
        self._create_test_executable(exec2_path, "Second executable")
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._verify_executable(self.output_path, executable_name)
            
            # One should be moved to root (whichever rglob finds first)
            root_executable = self.output_path / executable_name
            self.assertTrue(root_executable.exists())
            
            # Should log the move operation
            move_messages = [call[0][0] for call in mock_logger.info.call_args_list if "Moved executable" in call[0][0]]
            self.assertTrue(len(move_messages) > 0)

    def test_verify_executable_sets_permissions_unix(self):
        """Test _verify_executable sets executable permissions on Unix-like systems."""
        if not hasattr(os, 'chmod'):
            self.skipTest("os.chmod not available on this system")
        
        # Skip on Windows since file permissions work differently
        if os.name == 'nt':
            self.skipTest("Unix permission test skipped on Windows")
        
        executable_name = "permissions.exe"
        executable_path = self.output_path / executable_name
        self._create_test_executable(executable_path)
        
        # Reset permissions to non-executable
        executable_path.chmod(0o644)
        original_mode = executable_path.stat().st_mode & 0o777
        self.assertEqual(original_mode, 0o644)
        
        with patch.object(src_dependency_manager, 'logger'):
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Verify permissions were set to executable
            new_mode = executable_path.stat().st_mode & 0o777
            self.assertEqual(new_mode, 0o755)

    def test_verify_executable_logs_file_size(self):
        """Test _verify_executable logs the executable file size correctly."""
        executable_name = "sized.exe"
        executable_path = self.output_path / executable_name
        test_size = 4096
        self._create_test_executable(executable_path, size_bytes=test_size)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Check that size was logged correctly
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            size_log = next((call for call in info_calls if "Verified executable" in call), None)
            self.assertIsNotNone(size_log)
            self.assertIn(f"({test_size} bytes)", size_log)
            self.assertIn(str(executable_path), size_log)

    def test_verify_executable_handles_move_exception(self):
        """Test _verify_executable handles exceptions during file move operations."""
        executable_name = "move_error.exe"
        
        # Create executable in subdirectory
        subdir = self.output_path / "subdir"
        subdir.mkdir()
        executable_subpath = subdir / executable_name
        self._create_test_executable(executable_subpath)
        
        # Mock shutil.move to raise exception
        with patch('shutil.move', side_effect=PermissionError("Access denied")):
            with self.assertRaises(Exception) as context:
                self.dm._verify_executable(self.output_path, executable_name)
            
            # Should propagate the exception from shutil.move
            self.assertIn("Access denied", str(context.exception))

    def test_verify_executable_case_insensitive_search(self):
        """Test _verify_executable behavior with different case executable names."""
        # This test checks the current behavior - rglob should handle case sensitivity per OS
        executable_name = "App.EXE"
        
        # Create executable with exact case
        subdir = self.output_path / "bin"
        subdir.mkdir()
        executable_path = subdir / executable_name
        self._create_test_executable(executable_path)
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            # Search with exact case should work
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Verify it was found and moved
            root_executable = self.output_path / executable_name
            self.assertTrue(root_executable.exists())

    def test_verify_executable_empty_output_directory(self):
        """Test _verify_executable with completely empty output directory."""
        executable_name = "missing.exe"
        
        # Ensure output directory is empty
        for item in self.output_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        
        with self.assertRaises(Exception) as context:
            self.dm._verify_executable(self.output_path, executable_name)
        
        self.assertEqual(str(context.exception), f"Executable {executable_name} not found after extraction")

    def test_verify_executable_existing_file_at_destination(self):
        """Test _verify_executable when destination file already exists."""
        executable_name = "existing.exe"
        
        # Create executable at root (destination)
        root_executable = self.output_path / executable_name
        self._create_test_executable(root_executable, "Existing content", size_bytes=1024)
        
        # Create another executable in subdirectory with same name
        subdir = self.output_path / "subdir"
        subdir.mkdir()
        sub_executable = subdir / executable_name
        self._create_test_executable(sub_executable, "Subdirectory content")
        
        with patch.object(src_dependency_manager, 'logger') as mock_logger:
            self.dm._verify_executable(self.output_path, executable_name)
            
            # Root executable should still exist (found first, no move needed)
            self.assertTrue(root_executable.exists())
            self.assertEqual(root_executable.read_text(), "x" * 1024)  # Original content preserved
            
            # Should log verification of existing executable
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            verify_log = next((call for call in info_calls if "Verified executable" in call), None)
            self.assertIsNotNone(verify_log)

    @patch.object(src_dependency_manager, 'logger')
    def test_verify_executable_logs_verification_success(self, mock_logger):
        """Test that _verify_executable logs successful verification."""
        executable_name = "success.exe"
        executable_path = self.output_path / executable_name
        self._create_test_executable(executable_path, size_bytes=2048)
        
        self.dm._verify_executable(self.output_path, executable_name)
        
        # Verify success logging
        mock_logger.info.assert_called()
        info_message = mock_logger.info.call_args[0][0]
        self.assertIn("Verified executable:", info_message)
        self.assertIn(str(executable_path), info_message)
        self.assertIn("2048 bytes", info_message)


if __name__ == '__main__':
    unittest.main()