import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add the src directory to the Python path to import steam modules
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.steam.run_depot_downloader module to avoid conflicts
import importlib.util
spec = importlib.util.spec_from_file_location("src_run_depot_downloader", os.path.join(src_path, "steam", "run_depot_downloader.py"))
src_run_depot_downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_run_depot_downloader)

DepotDownloader = src_run_depot_downloader.DepotDownloader


class TestDepotDownloaderProcesses(unittest.TestCase):
    """Test cases for DepotDownloader external process functions"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        self.wrf_dir = str(self.test_path / "wrf_game")
        self.steam_username = "test_user"
        self.steam_password = "test_password"
        self.force = False
        
        # Create the wrf_dir
        Path(self.wrf_dir).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test directory
        if self.test_path.exists():
            shutil.rmtree(self.test_path)

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    def test_download(self, mock_run_process, mock_exists):
        """Test _download method constructs correct subprocess options."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        manifest_id = "123456789"
        
        with patch.object(src_run_depot_downloader, 'logger') as mock_logger:
            depot._download(manifest_id)
            
            # Verify logging
            mock_logger.debug.assert_called_with(f'Downloading game with manifest id {manifest_id}')
            
            # Verify run_process was called with correct options
            mock_run_process.assert_called_once()
            call_args = mock_run_process.call_args[0][0]
            
            expected_options = [
                os.path.join(depot.depot_downloader_cmd_path),
                '-app', depot.app_id,
                '-depot', depot.depot_id,
                '-manifest', manifest_id,
                '-username', self.steam_username,
                '-password', self.steam_password,
                '-remember-password',
                '-dir', self.wrf_dir,
            ]
            
            self.assertEqual(call_args, expected_options)
            
            # Verify the name option was passed
            call_kwargs = mock_run_process.call_args[1]
            self.assertEqual(call_kwargs['name'], 'download-game-files')

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    @patch('os.listdir')
    @patch('shutil.rmtree')
    def test_get_latest_manifest_id_success(self, mock_rmtree, mock_listdir, mock_run_process, mock_exists):
        """Test _get_latest_manifest_id successfully retrieves manifest ID."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        # Mock the manifest file in temp directory
        mock_manifest_filename = f"manifest_{depot.depot_id}_987654321.txt"
        mock_listdir.return_value = [mock_manifest_filename, "other_file.txt"]
        
        result = depot._get_latest_manifest_id()
        
        # Verify run_process was called with correct options for manifest-only
        mock_run_process.assert_called_once()
        call_args = mock_run_process.call_args[0][0]
        
        temp_dir = os.path.join(self.wrf_dir, 'temp')
        expected_options = [
            os.path.join(depot.depot_downloader_cmd_path),
            '-app', depot.app_id,
            '-depot', depot.depot_id,
            '-username', self.steam_username,
            '-password', self.steam_password,
            '-remember-password',
            '-dir', temp_dir,
            '-manifest-only',
            '-validate',
        ]
        
        self.assertEqual(call_args, expected_options)
        
        # Verify the name option was passed
        call_kwargs = mock_run_process.call_args[1]
        self.assertEqual(call_kwargs['name'], 'get-latest-manifest-id')
        
        # Verify manifest ID was correctly extracted
        self.assertEqual(result, "987654321")
        
        # Verify temp directory was cleaned up
        mock_rmtree.assert_called_once_with(temp_dir)

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    @patch('os.listdir')
    @patch('shutil.rmtree')
    def test_get_latest_manifest_id_multiple_manifests(self, mock_rmtree, mock_listdir, mock_run_process, mock_exists):
        """Test _get_latest_manifest_id with multiple manifest files (should pick last)."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        # Mock multiple manifest files - should pick the last one found (due to loop overwriting)
        mock_manifest_files = [
            f"manifest_{depot.depot_id}_111111111.txt",
            f"manifest_{depot.depot_id}_222222222.txt",
            "other_file.txt"
        ]
        mock_listdir.return_value = mock_manifest_files
        
        result = depot._get_latest_manifest_id()
        
        # Should return the last manifest ID found (due to implementation overwriting in loop)
        self.assertEqual(result, "222222222")

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    @patch('os.listdir')
    @patch('shutil.rmtree')
    def test_get_latest_manifest_id_no_manifest_files(self, mock_rmtree, mock_listdir, mock_run_process, mock_exists):
        """Test _get_latest_manifest_id when no manifest files are found."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        # Mock no manifest files found
        mock_listdir.return_value = ["other_file.txt", "readme.md"]
        
        result = depot._get_latest_manifest_id()
        
        # Should return None when no manifest files found
        self.assertIsNone(result)
        
        # Verify temp directory was still cleaned up
        temp_dir = os.path.join(self.wrf_dir, 'temp')
        mock_rmtree.assert_called_once_with(temp_dir)

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    @patch('os.listdir')
    @patch('shutil.rmtree')
    def test_get_latest_manifest_id_empty_directory(self, mock_rmtree, mock_listdir, mock_run_process, mock_exists):
        """Test _get_latest_manifest_id when temp directory is empty."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        # Mock empty directory
        mock_listdir.return_value = []
        
        result = depot._get_latest_manifest_id()
        
        # Should return None for empty directory
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    @patch('os.listdir')
    @patch('shutil.rmtree')
    def test_get_latest_manifest_id_manifest_filename_parsing(self, mock_rmtree, mock_listdir, mock_run_process, mock_exists):
        """Test _get_latest_manifest_id correctly parses different manifest filename formats."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        # Test various manifest filename formats
        test_cases = [
            (f"manifest_{depot.depot_id}_123456789.txt", "123456789"),
            ("manifest_1491005_999888777.txt", "999888777"),
            ("manifest_prefix_1491005_555444333.txt", "555444333"),  # Should get the last part after final underscore
        ]
        
        for filename, expected_id in test_cases:
            mock_listdir.return_value = [filename]
            result = depot._get_latest_manifest_id()
            self.assertEqual(result, expected_id, f"Failed to parse manifest ID from {filename}")

    @patch('os.path.exists')
    @patch.object(src_run_depot_downloader, 'run_process')
    def test_download_with_special_characters_in_credentials(self, mock_run_process, mock_exists):
        """Test _download handles special characters in username and password."""
        mock_exists.return_value = True
        
        special_username = "user@email.com"
        special_password = "pass!@#$%"
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=special_username,
            steam_password=special_password,
            force=self.force
        )
        
        manifest_id = "123456789"
        
        depot._download(manifest_id)
        
        # Verify run_process was called and options include special characters
        call_args = mock_run_process.call_args[0][0]
        
        # Find username and password in the options
        username_idx = call_args.index('-username')
        password_idx = call_args.index('-password')
        
        self.assertEqual(call_args[username_idx + 1], special_username)
        self.assertEqual(call_args[password_idx + 1], special_password)


if __name__ == '__main__':
    unittest.main()