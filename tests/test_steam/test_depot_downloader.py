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


class TestDepotDownloader(unittest.TestCase):
    """Test cases for DepotDownloader class"""
    
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
        
        # Mock DepotDownloader.exe existence
        self.depot_exe_path = "src/steam/DepotDownloader/DepotDownloader.exe"

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test directory
        if self.test_path.exists():
            shutil.rmtree(self.test_path)

    @patch('os.path.exists')
    def test_init_success(self, mock_exists):
        """Test successful DepotDownloader initialization."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        self.assertEqual(depot.wrf_dir, self.wrf_dir)
        self.assertEqual(depot.steam_username, self.steam_username)
        self.assertEqual(depot.steam_password, self.steam_password)
        self.assertEqual(depot.force, self.force)
        self.assertEqual(depot.app_id, '1491000')
        self.assertEqual(depot.depot_id, '1491005')
        self.assertEqual(depot.manifest_path, os.path.join(self.wrf_dir, 'manifest.txt'))

    @patch('os.path.exists')
    def test_init_depot_downloader_not_exists(self, mock_exists):
        """Test DepotDownloader initialization when DepotDownloader.exe doesn't exist."""
        mock_exists.return_value = False
        
        with self.assertRaises(Exception) as context:
            DepotDownloader(
                wrf_dir=self.wrf_dir,
                steam_username=self.steam_username,
                steam_password=self.steam_password,
                force=self.force
            )
        
        self.assertIn('Is DepotDownloader installed?', str(context.exception))

    @patch('os.path.exists')
    def test_init_missing_username(self, mock_exists):
        """Test DepotDownloader initialization with missing username."""
        mock_exists.return_value = True
        
        with self.assertRaises(Exception) as context:
            DepotDownloader(
                wrf_dir=self.wrf_dir,
                steam_username="",
                steam_password=self.steam_password,
                force=self.force
            )
        
        self.assertIn('Steam username and password are required', str(context.exception))

    @patch('os.path.exists')
    def test_init_missing_password(self, mock_exists):
        """Test DepotDownloader initialization with missing password."""
        mock_exists.return_value = True
        
        with self.assertRaises(Exception) as context:
            DepotDownloader(
                wrf_dir=self.wrf_dir,
                steam_username=self.steam_username,
                steam_password="",
                force=self.force
            )
        
        self.assertIn('Steam username and password are required', str(context.exception))

    @patch('os.path.exists')
    def test_init_missing_both_credentials(self, mock_exists):
        """Test DepotDownloader initialization with missing both username and password."""
        mock_exists.return_value = True
        
        with self.assertRaises(Exception) as context:
            DepotDownloader(
                wrf_dir=self.wrf_dir,
                steam_username=None,
                steam_password=None,
                force=self.force
            )
        
        self.assertIn('Steam username and password are required', str(context.exception))

    @patch('os.path.exists')
    def test_read_downloaded_manifest_id_file_exists(self, mock_exists):
        """Test _read_downloaded_manifest_id when manifest file exists."""
        mock_exists.side_effect = lambda path: path == self.depot_exe_path or path.endswith('manifest.txt')
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        manifest_content = "123456789"
        manifest_path = Path(self.wrf_dir) / "manifest.txt"
        manifest_path.write_text(manifest_content)
        
        # Mock os.path.exists for the manifest file specifically
        with patch('os.path.exists') as mock_manifest_exists:
            mock_manifest_exists.return_value = True
            with patch('builtins.open', mock_open(read_data=manifest_content)):
                result = depot._read_downloaded_manifest_id()
        
        self.assertEqual(result, manifest_content)

    @patch('os.path.exists')
    def test_read_downloaded_manifest_id_file_not_exists(self, mock_exists):
        """Test _read_downloaded_manifest_id when manifest file doesn't exist."""
        mock_exists.side_effect = lambda path: path == self.depot_exe_path
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        result = depot._read_downloaded_manifest_id()
        
        self.assertIsNone(result)

    @patch('os.path.exists')
    def test_read_downloaded_manifest_id_with_whitespace(self, mock_exists):
        """Test _read_downloaded_manifest_id strips whitespace from manifest content."""
        mock_exists.side_effect = lambda path: path == self.depot_exe_path or path.endswith('manifest.txt')
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        manifest_content = "  123456789  \n"
        
        with patch('os.path.exists') as mock_manifest_exists:
            mock_manifest_exists.return_value = True
            with patch('builtins.open', mock_open(read_data=manifest_content)):
                result = depot._read_downloaded_manifest_id()
        
        self.assertEqual(result, "123456789")

    @patch('os.path.exists')
    def test_write_downloaded_manifest_id(self, mock_exists):
        """Test _write_downloaded_manifest_id writes manifest ID to file."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=self.force
        )
        
        manifest_id = "987654321"
        
        with patch.object(src_run_depot_downloader, 'logger') as mock_logger:
            with patch('builtins.open', mock_open()) as mock_file:
                depot._write_downloaded_manifest_id(manifest_id)
                
                # Verify file was opened for writing
                mock_file.assert_called_once_with(depot.manifest_path, 'w')
                
                # Verify content was written
                handle = mock_file()
                handle.write.assert_called_once_with(manifest_id)
                
                # Verify logging
                mock_logger.debug.assert_called_once()

    @patch('os.path.exists')
    def test_run_with_manifest_id_already_downloaded_no_force(self, mock_exists):
        """Test run method when manifest is already downloaded and force is False."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=False
        )
        
        manifest_id = "123456789"
        
        with patch.object(depot, '_read_downloaded_manifest_id', return_value=manifest_id):
            with patch.object(depot, '_download') as mock_download:
                with patch.object(depot, '_write_downloaded_manifest_id') as mock_write:
                    with patch.object(src_run_depot_downloader, 'logger') as mock_logger:
                        depot.run(manifest_id)
                        
                        # Verify download and write were not called
                        mock_download.assert_not_called()
                        mock_write.assert_not_called()
                        
                        # Verify logging
                        mock_logger.info.assert_called_once_with(f'Already downloaded manifest {manifest_id}')

    @patch('os.path.exists')
    def test_run_with_manifest_id_already_downloaded_with_force(self, mock_exists):
        """Test run method when manifest is already downloaded but force is True."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=True
        )
        
        manifest_id = "123456789"
        
        with patch.object(depot, '_read_downloaded_manifest_id', return_value=manifest_id):
            with patch.object(depot, '_download') as mock_download:
                with patch.object(depot, '_write_downloaded_manifest_id') as mock_write:
                    depot.run(manifest_id)
                    
                    # Verify download and write were called
                    mock_download.assert_called_once_with(manifest_id)
                    mock_write.assert_called_once_with(manifest_id)

    @patch('os.path.exists')
    def test_run_with_different_manifest_id(self, mock_exists):
        """Test run method when a different manifest is already downloaded."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=False
        )
        
        old_manifest_id = "123456789"
        new_manifest_id = "987654321"
        
        with patch.object(depot, '_read_downloaded_manifest_id', return_value=old_manifest_id):
            with patch.object(depot, '_download') as mock_download:
                with patch.object(depot, '_write_downloaded_manifest_id') as mock_write:
                    depot.run(new_manifest_id)
                    
                    # Verify download and write were called with new manifest
                    mock_download.assert_called_once_with(new_manifest_id)
                    mock_write.assert_called_once_with(new_manifest_id)

    @patch('os.path.exists')
    def test_run_with_no_manifest_id(self, mock_exists):
        """Test run method when no manifest ID is provided (should get latest)."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=False
        )
        
        latest_manifest_id = "999888777"
        
        with patch.object(depot, '_get_latest_manifest_id', return_value=latest_manifest_id):
            with patch.object(depot, '_read_downloaded_manifest_id', return_value=None):
                with patch.object(depot, '_download') as mock_download:
                    with patch.object(depot, '_write_downloaded_manifest_id') as mock_write:
                        with patch.object(src_run_depot_downloader, 'logger') as mock_logger:
                            depot.run(None)
                            
                            # Verify latest manifest was retrieved
                            mock_logger.debug.assert_called_with(f"DepotDownloader retrieved latest manifest id of: {latest_manifest_id}")
                            
                            # Verify download and write were called with latest manifest
                            mock_download.assert_called_once_with(latest_manifest_id)
                            mock_write.assert_called_once_with(latest_manifest_id)

    @patch('os.path.exists')
    def test_run_no_previous_manifest(self, mock_exists):
        """Test run method when no previous manifest exists."""
        mock_exists.return_value = True
        
        depot = DepotDownloader(
            wrf_dir=self.wrf_dir,
            steam_username=self.steam_username,
            steam_password=self.steam_password,
            force=False
        )
        
        manifest_id = "555444333"
        
        with patch.object(depot, '_read_downloaded_manifest_id', return_value=None):
            with patch.object(depot, '_download') as mock_download:
                with patch.object(depot, '_write_downloaded_manifest_id') as mock_write:
                    depot.run(manifest_id)
                    
                    # Verify download and write were called
                    mock_download.assert_called_once_with(manifest_id)
                    mock_write.assert_called_once_with(manifest_id)


if __name__ == '__main__':
    unittest.main()