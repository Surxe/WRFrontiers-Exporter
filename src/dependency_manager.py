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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import run_process
from loguru import logger


class DependencyManager:
    """
    A dependency manager that downloads and extracts GitHub release dependencies.
    
    This class handles downloading ZIP files from GitHub releases and extracting them
    to specified output directories with proper validation and cleanup.
    """
    
    def __init__(self):
        """Initialize the dependency manager."""
        self.temp_dir = Path.cwd() / ".temp_downloads"
        self.temp_dir.mkdir(exist_ok=True)
    
    def download_and_extract(self, download_url, output_path, executable_name=None, create_output_dir=True):
        """
        Download a ZIP file from a URL and extract it to the specified path.
        
        Args:
            download_url (str): URL to download the ZIP file from
            output_path (str or Path): Directory to extract the contents to
            executable_name (str, optional): Name of main executable to verify after extraction
            create_output_dir (bool): Whether to create the output directory if it doesn't exist
            
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
            
            # Check if executable already exists
            if executable_name and (output_path / executable_name).exists():
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
    
    def download_github_release_latest(self, repo_owner, repo_name, asset_pattern, output_path, executable_name=None):
        """
        Download the latest release from a GitHub repository.
        
        Args:
            repo_owner (str): GitHub repository owner
            repo_name (str): GitHub repository name
            asset_pattern (str): Pattern to match asset name (e.g., "windows-x64.zip")
            output_path (str or Path): Directory to extract to
            executable_name (str, optional): Name of main executable to verify
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get latest release info
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            logger.info(f"Fetching latest release info from: {api_url}")
            
            release_info = self._get_json_from_url(api_url)
            version = release_info.get('tag_name', 'unknown')
            
            logger.info(f"Latest version: {version}")
            
            # Find matching asset
            assets = release_info.get('assets', [])
            matching_asset = None
            
            for asset in assets:
                if asset_pattern in asset['name']:
                    matching_asset = asset
                    break
            
            if not matching_asset:
                raise Exception(f"No asset found matching pattern: {asset_pattern}")
            
            download_url = matching_asset['browser_download_url']
            logger.info(f"Found matching asset: {matching_asset['name']}")
            
            return self.download_and_extract(download_url, output_path, executable_name)
            
        except Exception as e:
            logger.error(f"Failed to download latest release: {e}")
            raise
    
    def _get_filename_from_url(self, url):
        """Extract filename from URL."""
        return Path(url).name or "download.zip"
    
    def _download_file(self, url, output_path):
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
    
    def _get_json_from_url(self, url):
        """Get JSON data from URL."""
        try:
            req = Request(url, headers={'User-Agent': 'WRFrontiers-Exporter'})
            with urlopen(req) as response:
                return json.loads(response.read().decode())
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to fetch JSON from {url}: {e}")
    
    def _validate_zip_file(self, zip_path):
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
    
    def _extract_zip(self, zip_path, output_path):
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
    
    def _flatten_extraction(self, output_path):
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
    
    def _verify_executable(self, output_path, executable_name):
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
    
    def cleanup_temp_files(self):
        """Clean up temporary download directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.debug("Cleaned up temporary download directory")


def install_batch_export(output_path=None):
    """
    Install BatchExport dependency.
    
    Args:
        output_path (str, optional): Path to install to. Defaults to src/cue4p-batchexport/BatchExport/
    """
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir / "cue4p-batchexport" / "BatchExport"
    
    dm = DependencyManager()
    try:
        return dm.download_github_release_latest(
            repo_owner="Surxe",
            repo_name="CUE4P-BatchExport", 
            asset_pattern="BatchExport-windows-x64.zip",
            output_path=output_path,
            executable_name="BatchExport.exe"
        )
    finally:
        dm.cleanup_temp_files()


def install_depot_downloader(output_path=None):
    """
    Install DepotDownloader dependency from the latest GitHub release.
    
    Args:
        output_path (str, optional): Path to install to. Defaults to src/steam/DepotDownloader/
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
            executable_name="DepotDownloader.exe"
        )
    finally:
        dm.cleanup_temp_files()


def main():
    """Main function to install all dependencies."""
    logger.info("Installing WRFrontiers-Exporter dependencies...")
    
    try:
        # Install BatchExport
        logger.info("Installing BatchExport...")
        install_batch_export()
        
        # Install DepotDownloader
        logger.info("Installing DepotDownloader...")
        install_depot_downloader()
        
        logger.success("All dependencies installed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WRFrontiers-Exporter Dependency Manager")
    parser.add_argument("--url", help="Direct download URL for a dependency")
    parser.add_argument("--output", help="Output path to extract dependency to")
    parser.add_argument("--executable", help="Name of main executable to verify after extraction")
    parser.add_argument("--batch-export-only", action="store_true", help="Install only BatchExport dependency")
    parser.add_argument("--depot-downloader-only", action="store_true", help="Install only DepotDownloader dependency")
    
    args = parser.parse_args()
    
    # If specific URL provided, use direct download
    if args.url and args.output:
        dm = DependencyManager()
        try:
            success = dm.download_and_extract(
                download_url=args.url,
                output_path=args.output,
                executable_name=args.executable
            )
            if success:
                logger.success("Dependency installed successfully!")
            else:
                logger.error("Failed to install dependency")
        finally:
            dm.cleanup_temp_files()
    
    # Install specific dependencies
    elif args.batch_export_only:
        logger.info("Installing BatchExport only...")
        install_batch_export(args.output)
    
    elif args.depot_downloader_only:
        logger.info("Installing DepotDownloader only...")
        install_depot_downloader(args.output)
    
    # Default: install all dependencies
    else:
        main()