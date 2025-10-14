# Add parent dir to sys path
import sys
import os
import time
import zipfile
import shutil
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
from typing import Optional, Union, List
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger


class DependencyManager:
    """
    A dependency manager that downloads and extracts GitHub release dependencies.
    
    This class handles downloading ZIP files from GitHub releases and extracting them
    to specified output directories with proper validation and cleanup.
    """
    
    def __init__(self) -> None:
        """Initialize the dependency manager."""
        self.temp_dir = Path.cwd() / ".temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def _get_installed_version(self, output_path: Union[str, Path]) -> Optional[str]:
        """
        Get the currently installed version from version.txt file.
        
        Args:
            output_path (Path): Directory where dependency is installed
            
        Returns:
            str or None: Version string if found, None if file doesn't exist
        """
        version_file = Path(output_path) / "version.txt"
        if version_file.exists():
            try:
                return version_file.read_text().strip()
            except Exception as e:
                logger.warning(f"Could not read version file {version_file}: {e}")
                return None
        return None
    
    def _write_version_file(self, output_path: Union[str, Path], version: str) -> None:
        """
        Write the version to version.txt file in the output directory.
        
        Args:
            output_path (Path): Directory where dependency is installed
            version (str): Version string to write
        """
        try:
            version_file = Path(output_path) / "version.txt"
            version_file.write_text(version)
            logger.debug(f"Wrote version {version} to {version_file}")
        except Exception as e:
            logger.warning(f"Could not write version file: {e}")
    
    def download_and_extract(self, download_url: str, output_path: Union[str, Path], executable_name: Optional[str] = None, create_output_dir: bool = True, version: Optional[str] = None) -> bool:
        """
        Download a ZIP file from a URL and extract it to the specified path.
        
        Args:
            download_url (str): URL to download the ZIP file from
            output_path (str or Path): Directory to extract the contents to
            executable_name (str, optional): Name of main executable to verify after extraction
            create_output_dir (bool): Whether to create the output directory if it doesn't exist
            version (str, optional): Version string to write to version.txt file
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            Exception: If download or extraction fails
        """
        start_time = time.time()
        logger.debug(f"Dependency download timer started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        
        output_path = Path(output_path)
        
        try:
            # Create output directory if needed
            if create_output_dir:
                output_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {output_path}")
            
            # Check if we should skip installation based on version
            if version:
                installed_version = self._get_installed_version(output_path)
                if installed_version == version:
                    logger.info(f"Version {version} already installed, skipping download")
                    return True
                elif installed_version:
                    logger.info(f"Updating from version {installed_version} to {version}")
                else:
                    logger.info(f"Installing version {version} (no previous version found)")
            
            # Check if executable already exists (fallback if no version provided)
            elif executable_name and (output_path / executable_name).exists():
                logger.info(f"Executable {executable_name} already exists at: {output_path / executable_name}")
                logger.info("To reinstall, delete the executable and run this again.")
                return True
            
            # Download the file
            zip_filename = self._get_filename_from_url(download_url)
            zip_path = self.temp_dir / zip_filename
            
            logger.info(f"Downloading from: {download_url}")
            logger.info(f"Output directory: {output_path}")
            
            self._download_file(download_url, zip_path)
            
            # Validate the downloaded file
            if not self._validate_zip_file(zip_path):
                raise Exception("Downloaded file is not a valid ZIP archive")
            
            # Extract the file
            logger.info("Extracting files...")
            self._extract_zip(zip_path, output_path)
            
            # Verify extraction
            if executable_name:
                self._verify_executable(output_path, executable_name)
            
            # Write version file if version provided
            if version:
                self._write_version_file(output_path, version)
            
            # Cleanup
            zip_path.unlink()
            logger.info("Cleaned up temporary files")
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.debug(f"Dependency download timer ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
            logger.debug(f"Total dependency download time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
            
            logger.success("Dependency installed successfully!")
            return True
            
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.debug(f"Dependency download timer ended (with error) at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
            logger.debug(f"Dependency download time before error: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
            
            logger.error(f"Failed to install dependency: {e}")
            # Cleanup on failure
            if 'zip_path' in locals() and zip_path.exists():
                zip_path.unlink()
            raise
    
    def download_github_release_latest(self, repo_owner: str, repo_name: str, asset_pattern: Union[str, List[str]], output_path: Union[str, Path], executable_name: Optional[str] = None, force: bool = False) -> bool:
        """
        Download the latest release from a GitHub repository.
        
        Args:
            repo_owner (str): GitHub repository owner
            repo_name (str): GitHub repository name
            asset_pattern (str or list): Pattern(s) to match asset name (e.g., "windows-x64.zip" or ["BatchExport-windows-x64.zip", "README.md"])
            output_path (str or Path): Directory to extract to
            executable_name (str, optional): Name of main executable to verify
            force (bool): Force download even if same version exists
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            
            # Get latest release info
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            logger.info(f"Fetching latest release info from: {api_url}")
            
            release_info = self._get_json_from_url(api_url)
            version = release_info.get('tag_name', 'unknown')
            
            logger.info(f"Latest version: {version}")
            
            # Check if we already have this version (unless force is True)
            if not force:
                current_version = self._get_installed_version(output_path)
                if current_version == version:
                    logger.info(f"Version {version} already installed. Skipping download.")
                    return True
                elif current_version:
                    logger.info(f"Updating from version {current_version} to {version}")
            else:
                logger.info("Force download enabled, downloading regardless of current version")
            
            # Find matching assets
            assets = release_info.get('assets', [])
            matching_assets = []
            
            # Normalize asset_pattern to a list
            patterns = asset_pattern if isinstance(asset_pattern, list) else [asset_pattern]
            
            for pattern in patterns:
                for asset in assets:
                    if pattern in asset['name']:
                        matching_assets.append(asset)
                        logger.info(f"Found matching asset: {asset['name']} (pattern: {pattern})")
                        break
                else:
                    # This pattern didn't match any asset
                    logger.warning(f"No asset found matching pattern: {pattern}")
            
            if not matching_assets:
                raise Exception(f"No assets found matching patterns: {patterns}")
            
            # Download and extract all matching assets
            success = True
            for asset in matching_assets:
                download_url = asset['browser_download_url']
                logger.info(f"Processing asset: {asset['name']}")
                
                try:
                    # For non-ZIP files (like README.md), just download them directly
                    if not asset['name'].lower().endswith('.zip'):
                        self._download_single_file(download_url, output_path / asset['name'])
                    else:
                        # For ZIP files, use the existing extraction logic
                        result = self.download_and_extract(download_url, output_path, executable_name, version=version)
                        if not result:
                            success = False
                except Exception as e:
                    logger.error(f"Failed to process asset {asset['name']}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to download latest release: {e}")
            raise
    
    def _download_single_file(self, url: str, output_path: Path) -> None:
        """
        Download a single file (non-ZIP) from URL to output path.
        
        Args:
            url (str): URL to download from
            output_path (Path): Full path including filename to save to
        """
        try:
            logger.info(f"Downloading single file: {output_path.name}")
            
            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the file
            req = Request(url, headers={'User-Agent': 'WRFrontiers-Exporter'})
            
            with urlopen(req) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            
            file_size = output_path.stat().st_size
            logger.info(f"Downloaded {output_path.name} ({file_size} bytes)")
            
        except Exception as e:
            raise Exception(f"Failed to download single file: {e}")

    def _get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        return Path(url).name or "download.zip"
    
    def _download_file(self, url: str, output_path: Path) -> None:
        """Download a file from URL to local path."""
        try:
            logger.info(f"Downloading file...")
            
            # Create request with user agent to avoid GitHub API restrictions
            req = Request(url, headers={'User-Agent': 'WRFrontiers-Exporter'})
            
            with urlopen(req) as response:
                file_size = int(response.headers.get('Content-Length', 0))
                
                with open(output_path, 'wb') as f:
                    downloaded = 0
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if file_size > 0:
                            progress = (downloaded / file_size) * 100
                            if downloaded % (chunk_size * 100) == 0:  # Log every ~800KB
                                logger.debug(f"Download progress: {progress:.1f}% ({downloaded}/{file_size} bytes)")
            
            actual_size = output_path.stat().st_size
            logger.info(f"Downloaded {output_path.name} ({actual_size} bytes)")
            
        except (URLError, HTTPError) as e:
            raise Exception(f"Failed to download file: {e}")
    
    def _get_json_from_url(self, url: str) -> dict:
        """Get JSON data from URL."""
        try:
            req = Request(url, headers={'User-Agent': 'WRFrontiers-Exporter'})
            with urlopen(req) as response:
                return json.loads(response.read().decode())
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to fetch JSON from {url}: {e}")
    
    def _validate_zip_file(self, zip_path: Path) -> bool:
        """Validate that the file is a proper ZIP archive."""
        try:
            file_size = zip_path.stat().st_size
            logger.debug(f"Validating ZIP file: {zip_path.name} ({file_size} bytes)")
            
            # Check if file is too small (likely an error page)
            if file_size < 1000:
                logger.error(f"File is too small ({file_size} bytes), likely an error page")
                return False
            
            # Test if it's a valid ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Try to read the file list
                file_list = zf.namelist()
                logger.debug(f"ZIP contains {len(file_list)} files")
                return True
                
        except zipfile.BadZipFile:
            logger.error("File is not a valid ZIP archive")
            return False
        except Exception as e:
            logger.error(f"Error validating ZIP file: {e}")
            return False
    
    def _extract_zip(self, zip_path: Path, output_path: Path) -> None:
        """Extract ZIP file to output directory."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Log contents
                file_list = zf.namelist()
                logger.debug("Archive contents:")
                for filename in file_list[:10]:  # Show first 10 files
                    logger.debug(f"  {filename}")
                if len(file_list) > 10:
                    logger.debug(f"  ... and {len(file_list) - 10} more files")
                
                # Extract all files
                zf.extractall(output_path)
                
                # Flatten structure if everything is in a single subdirectory
                self._flatten_extraction(output_path)
                
                logger.info(f"Extracted {len(file_list)} files to {output_path}")
                
        except Exception as e:
            raise Exception(f"Failed to extract ZIP file: {e}")
    
    def _flatten_extraction(self, output_path: Path) -> None:
        """
        If extraction created a single subdirectory containing all files,
        move the files up to the main output directory.
        """
        subdirs = [d for d in output_path.iterdir() if d.is_dir()]
        files = [f for f in output_path.iterdir() if f.is_file()]
        
        # If there's exactly one subdirectory and no files in root, flatten it
        if len(subdirs) == 1 and len(files) == 0:
            subdir = subdirs[0]
            logger.debug(f"Flattening single subdirectory: {subdir.name}")
            
            # Move all files from subdirectory to parent
            for item in subdir.iterdir():
                dest = output_path / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            
            # Remove empty subdirectory
            subdir.rmdir()
            logger.debug("Flattened directory structure")
    
    def _verify_executable(self, output_path: Path, executable_name: str) -> None:
        """Verify that the expected executable was extracted."""
        executable_path = output_path / executable_name
        
        if not executable_path.exists():
            # Search for the executable in subdirectories
            found_executables = list(output_path.rglob(executable_name))
            if found_executables:
                # Move the first found executable to the root
                src = found_executables[0]
                shutil.move(str(src), str(executable_path))
                logger.info(f"Moved executable from {src.relative_to(output_path)} to root")
            else:
                raise Exception(f"Executable {executable_name} not found after extraction")
        
        file_size = executable_path.stat().st_size
        logger.info(f"Verified executable: {executable_path} ({file_size} bytes)")
        
        # Make executable on Unix-like systems
        if hasattr(os, 'chmod'):
            executable_path.chmod(0o755)
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary download directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.debug("Cleaned up temporary download directory")


def install_batch_export(output_path: Optional[Union[str, Path]] = None, force: bool = False) -> bool:
    """
    Install BatchExport dependency.
    
    Args:
        output_path (str, optional): Path to install to. Defaults to src/batch_export/BatchExport/
        force (bool): Force download even if same version exists
    """
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir / "batch_export" / "BatchExport"
    
    dm = DependencyManager()
    try:
        return dm.download_github_release_latest(
            repo_owner="Surxe",
            repo_name="CUE4P-BatchExport", 
            asset_pattern=["BatchExport-windows-x64.zip", "README.md"],
            output_path=output_path,
            executable_name="BatchExport.exe",
            force=force
        )
    finally:
        dm.cleanup_temp_files()


def install_depot_downloader(output_path: Optional[Union[str, Path]] = None, force: bool = False) -> bool:
    """
    Install DepotDownloader dependency from the latest GitHub release.
    
    Args:
        output_path (str, optional): Path to install to. Defaults to src/steam/DepotDownloader/
        force (bool): Force download even if same version exists
    """
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir / "steam" / "DepotDownloader"
    
    dm = DependencyManager()
    try:
        return dm.download_github_release_latest(
            repo_owner="SteamRE",
            repo_name="DepotDownloader",
            asset_pattern="windows-x64.zip",
            output_path=output_path,
            executable_name="DepotDownloader.exe",
            force=force
        )
    finally:
        dm.cleanup_temp_files()


def main(force_download: bool = False) -> bool:
    """
    Main function to install all dependencies.
    
    Args:
        force_download (bool): Force download even if same version exists
    """
    logger.info("Installing WRFrontiers-Exporter dependencies...")
    
    try:
        # Install BatchExport
        logger.info("Installing BatchExport...")
        install_batch_export(force=force_download)
        
        # Install DepotDownloader
        logger.info("Installing DepotDownloader...")
        install_depot_downloader(force=force_download)
        
        logger.success("All dependencies installed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()