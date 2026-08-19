# Add parent dir to sys path
import sys
import os
import time
import zipfile
import tarfile
import shutil
import subprocess
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

            # Extract the file (dispatch on archive type: .zip or .tar.gz/.tgz)
            logger.info("Extracting files...")
            lower_name = zip_path.name.lower()
            if lower_name.endswith('.tar.gz') or lower_name.endswith('.tgz'):
                self._extract_tar(zip_path, output_path)
            else:
                if not self._validate_zip_file(zip_path):
                    raise Exception("Downloaded file is not a valid ZIP archive")
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
    
    def download_github_release_latest(self, repo_owner: str, repo_name: str, asset_pattern: Union[str, List[str]], output_path: Union[str, Path], executable_name: Optional[str] = None, force: bool = False, release_tag: Optional[str] = None) -> bool:
        """
        Download the latest release from a GitHub repository.

        Args:
            repo_owner (str): GitHub repository owner
            repo_name (str): GitHub repository name
            asset_pattern (str or list): Pattern(s) to match asset name (e.g., "windows-x64.zip" or ["BatchExport-windows-x64.zip", "README.md"])
            output_path (str or Path): Directory to extract to
            executable_name (str, optional): Name of main executable to verify
            force (bool): Force download even if same version exists
            release_tag (str, optional): Specific release tag to target (e.g., "experimental-latest").
                If None, uses /releases/latest which skips pre-releases.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)

            # Get release info — either a specific tag or the latest stable release
            if release_tag:
                api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{release_tag}"
            else:
                api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            logger.info(f"Fetching release info from: {api_url}")
            
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
                    # Extract recognized archives; download everything else (README.md) as-is
                    name_lower = asset['name'].lower()
                    is_archive = name_lower.endswith('.zip') or name_lower.endswith('.tar.gz') or name_lower.endswith('.tgz')
                    if not is_archive:
                        self._download_single_file(download_url, output_path / asset['name'])
                    else:
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
    
    def _extract_tar(self, tar_path: Path, output_path: Path) -> None:
        """Extract a .tar.gz/.tgz archive to output directory, preserving perms."""
        try:
            with tarfile.open(tar_path, 'r:gz') as tf:
                members = tf.getnames()
                logger.debug("Archive contents:")
                for name in members[:10]:
                    logger.debug(f"  {name}")
                if len(members) > 10:
                    logger.debug(f"  ... and {len(members) - 10} more files")

                # 'data' filter (Python 3.12+) blocks unsafe absolute/parent paths.
                # Fall back to a plain extractall on older interpreters.
                try:
                    tf.extractall(output_path, filter='data')
                except TypeError:
                    tf.extractall(output_path)

                # Flatten structure if everything is in a single subdirectory
                self._flatten_extraction(output_path)

                logger.info(f"Extracted {len(members)} files to {output_path}")

        except Exception as e:
            raise Exception(f"Failed to extract tar.gz file: {e}")

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

    from utils import get_platform_key, executable_name

    # Platform-aware asset: linux ships a .tar.gz, windows a .zip
    plat = get_platform_key()  # e.g. "linux-x64", "windows-x64"
    archive_ext = "zip" if plat.startswith("windows") else "tar.gz"

    dm = DependencyManager()
    try:
        result = dm.download_github_release_latest(
            repo_owner="Surxe",
            repo_name="CUE4P-BatchExport",
            asset_pattern=[f"BatchExport-{plat}.{archive_ext}", "README.md"],
            output_path=output_path,
            executable_name=executable_name("BatchExport"),
            force=force
        )
    finally:
        dm.cleanup_temp_files()

    if not result:
        return False

    # On Linux, CUE4Parse's bundled Oodle/Detex native libs are Windows-only.
    # Provide Linux equivalents next to the binary so pak/texture decompression works.
    if plat.startswith("linux"):
        result = install_batch_export_native_libs(Path(output_path), force=force) and result

    return result


# OodleUE release providing the Linux Oodle shared object (mirrors CUE4Parse's
# own source: FabianFG/CUE4Parse OodleHelper.cs RELEASE_URL + LINUX_ZIP).
_OODLE_RELEASE = "2026-06-04-1357"
_OODLE_LINUX_ZIP_URL = f"https://github.com/WorkingRobot/OodleUE/releases/download/{_OODLE_RELEASE}/gcc-x64-release.zip"
_DETEX_REPO = "https://github.com/hglm/detex.git"

# SkiaSharp native library, used by CUE4Parse-Conversion to ENCODE decoded texture
# pixels into PNG (Detex only decodes BCn -> raw). The linux-x64 BatchExport single-
# file bundle ships the managed SkiaSharp.dll but not the native libSkiaSharp.so, so
# PNG texture export fails without it. We fetch the matching native lib from the
# NuGet package and drop it next to the binary.
# The version must match the managed SkiaSharp the build was compiled against —
# re-derive after a BatchExport update with:
#   strings BatchExport | grep -oiE 'SkiaSharp/[0-9.]+'
# The '.NoDependencies' variant is fully self-contained (no fontconfig/freetype),
# which is all texture export needs.
_SKIASHARP_VERSION = "3.119.1"
_SKIASHARP_NUPKG_URL = (
    "https://www.nuget.org/api/v2/package/"
    f"SkiaSharp.NativeAssets.Linux.NoDependencies/{_SKIASHARP_VERSION}"
)


def install_batch_export_native_libs(be_dir: Path, force: bool = False) -> bool:
    """
    Install the Linux native decompression libraries next to the BatchExport binary.

    CUE4Parse loads Oodle and Detex by bare filename via dlopen, so both must sit
    on LD_LIBRARY_PATH (run_batch_export adds be_dir). The tool loads them under
    their Windows names ('oodle-data-shared.dll', 'Detex.dll') but dlopen reads
    ELF content regardless of extension, so we save Linux .so content under those
    names.

    - Oodle: downloaded from WorkingRobot/OodleUE (the same release CUE4Parse uses),
      extracting lib/liboodle-data-shared.so.
    - Detex: built from source (hglm/detex) — CUE4Parse ships no Linux Detex. Needs
      git + a C compiler; if unavailable, logs a warning (texture export will fail
      but data/JSON export still works).
    - libSkiaSharp: extracted from the SkiaSharp NuGet package — the linux-x64
      BatchExport bundle omits it, so PNG texture encoding fails without it.
      Saved as 'libSkiaSharp.so' (the name SkiaSharp's P/Invoke dlopen()s).
      Best-effort; failure only warns (texture export will fail, data/JSON is
      unaffected).

    Returns True if Oodle installed (the hard requirement); Detex/SkiaSharp
    failures only warn.
    """
    # Absolute paths: the Detex build runs gcc with cwd set to a temp dir,
    # so a relative output path would resolve against the wrong directory.
    be_dir = Path(be_dir).resolve()
    oodle_dst = be_dir / "oodle-data-shared.dll"   # name the tool dlopen()s
    detex_dst = be_dir / "Detex.dll"               # name the tool dlopen()s
    skia_dst = be_dir / "libSkiaSharp.so"          # name SkiaSharp P/Invoke dlopen()s

    # --- Oodle (required) ---
    if oodle_dst.exists() and not force:
        logger.info(f"Oodle already present at {oodle_dst}")
    else:
        logger.info("Downloading Linux Oodle library from OodleUE...")
        dm = DependencyManager()
        try:
            oodle_tmp = dm.temp_dir / "oodle"
            oodle_tmp.mkdir(parents=True, exist_ok=True)
            zip_path = oodle_tmp / "gcc-x64-release.zip"
            dm._download_file(_OODLE_LINUX_ZIP_URL, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Locate the data-shared .so entry regardless of nesting
                entry = next((n for n in zf.namelist() if n.endswith("liboodle-data-shared.so")), None)
                if not entry:
                    logger.error("liboodle-data-shared.so not found in OodleUE zip")
                    return False
                with zf.open(entry) as src, open(oodle_dst, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            os.chmod(oodle_dst, 0o755)
            logger.info(f"Oodle installed to {oodle_dst}")
        finally:
            dm.cleanup_temp_files()

    # --- Detex (best-effort; only needed for texture export) ---
    if detex_dst.exists() and not force:
        logger.info(f"Detex already present at {detex_dst}")
    else:
        if not shutil.which("gcc") or not shutil.which("git"):
            logger.warning(
                "gcc and/or git not available — skipping Detex build. "
                "Texture export will fail; data/JSON export is unaffected."
            )
        else:
            logger.info("Building Linux Detex library from source...")
            try:
                detex_tmp = Path(DependencyManager().temp_dir) / "detex_build"
                if detex_tmp.exists():
                    shutil.rmtree(detex_tmp)
                subprocess.run(["git", "clone", "--depth", "1", _DETEX_REPO, str(detex_tmp)],
                               check=True, capture_output=True)
                # The library translation units (the detex Makefile's module list) —
                # excludes the standalone CLI programs (detex-convert.c, detex-view.c,
                # validate.c) which carry their own main().
                modules = [
                    "bptc-tables", "bits", "clamp", "convert", "dds",
                    "decompress-bc", "decompress-bptc", "decompress-bptc-float",
                    "decompress-etc", "decompress-eac", "decompress-rgtc",
                    "division-tables", "file-info", "half-float", "hdr", "ktx",
                    "misc", "raw", "texture",
                ]
                objs = []
                for m in modules:
                    subprocess.run(["gcc", "-c", "-fPIC", "-std=c99",
                                    "-D_POSIX_C_SOURCE=200809L", "-w", "-I.", "-O2",
                                    f"{m}.c", "-o", f"{m}.o"],
                                   check=True, cwd=str(detex_tmp), capture_output=True)
                    objs.append(f"{m}.o")
                subprocess.run(["gcc", "-shared", "-o", str(detex_dst)] + objs,
                               check=True, cwd=str(detex_tmp), capture_output=True)
                os.chmod(detex_dst, 0o755)
                logger.info(f"Detex built and installed to {detex_dst}")
            except subprocess.CalledProcessError as e:
                logger.warning(
                    f"Detex build failed ({e}); texture export will fail. "
                    "Data/JSON export is unaffected."
                )
            except Exception as e:
                logger.warning(f"Detex build error ({e}); texture export will fail.")

    # --- libSkiaSharp (best-effort; only needed for PNG texture encoding) ---
    if skia_dst.exists() and not force:
        logger.info(f"libSkiaSharp already present at {skia_dst}")
    else:
        logger.info(f"Downloading libSkiaSharp {_SKIASHARP_VERSION} from NuGet...")
        dm = DependencyManager()
        try:
            skia_tmp = dm.temp_dir / "skiasharp"
            skia_tmp.mkdir(parents=True, exist_ok=True)
            nupkg_path = skia_tmp / "skiasharp.nupkg"
            dm._download_file(_SKIASHARP_NUPKG_URL, nupkg_path)
            with zipfile.ZipFile(nupkg_path) as zf:
                entry = "runtimes/linux-x64/native/libSkiaSharp.so"
                if entry not in zf.namelist():
                    logger.warning(
                        f"{entry} not found in SkiaSharp nupkg; texture export will "
                        "fail. Data/JSON export is unaffected."
                    )
                else:
                    with zf.open(entry) as src, open(skia_dst, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    os.chmod(skia_dst, 0o755)
                    logger.info(f"libSkiaSharp installed to {skia_dst}")
        except Exception as e:
            logger.warning(
                f"libSkiaSharp install failed ({e}); texture export will fail. "
                "Data/JSON export is unaffected."
            )
        finally:
            dm.cleanup_temp_files()

    return oodle_dst.exists()


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
    
    from utils import get_platform_key, executable_name

    dm = DependencyManager()
    try:
        return dm.download_github_release_latest(
            repo_owner="SteamRE",
            repo_name="DepotDownloader",
            asset_pattern=f"DepotDownloader-{get_platform_key()}.zip",
            output_path=output_path,
            executable_name=executable_name("DepotDownloader"),
            force=force
        )
    finally:
        dm.cleanup_temp_files()


def install_ue4ss(output_path: Optional[Union[str, Path]] = None, force: bool = False) -> bool:
    """
    Install UE4SS (RE-UE4SS) dependency from the experimental-latest GitHub release.

    The experimental build supports UE5.4 while the stable v3.0.1 only goes up to
    UE5.3 (WRFrontiers is UE5.4).

    Zip layout: the experimental zip ships dwmapi.dll (the proxy loader) at its
    root plus a "ue4ss/" subdirectory containing UE4SS.dll, Mods/ and the
    settings ini.  We extract to a temp dir and assemble a flat staging dir at
    src/mapper/ue4ss/ containing everything deploy() needs:
        src/mapper/ue4ss/dwmapi.dll   (from zip root)
        src/mapper/ue4ss/UE4SS.dll    (from zip's ue4ss/)
        src/mapper/ue4ss/Mods/, UE4SS-settings.ini, ...

    Linux only — on Windows the Dumper-7 DLL injection path is used instead.

    Args:
        output_path (str, optional): Staging directory. Defaults to src/mapper/ue4ss/
        force (bool): Force download even if same version exists
    """
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir / "mapper" / "ue4ss"

    output_path = Path(output_path)

    # Skip if already installed at the target version (unless forced)
    version_file = output_path / "version.txt"
    dm = DependencyManager()
    try:
        # Extract into a temp dir, then assemble the staging dir from it
        stage_temp = dm.temp_dir / "ue4ss_stage"
        if stage_temp.exists():
            shutil.rmtree(stage_temp)
        stage_temp.mkdir(parents=True, exist_ok=True)

        result = dm.download_github_release_latest(
            repo_owner="UE4SS-RE",
            repo_name="RE-UE4SS",
            asset_pattern="UE4SS_v",
            output_path=stage_temp,
            executable_name=None,
            force=force,
            release_tag="experimental-latest",
        )
        if not result:
            return False

        # Assemble the flat staging dir. The zip gives us:
        #   stage_temp/dwmapi.dll   and   stage_temp/ue4ss/<payload>
        inner = stage_temp / "ue4ss"
        if not inner.is_dir():
            logger.error(f"Expected 'ue4ss/' dir in UE4SS zip, not found in {stage_temp}")
            return False

        # Reset the staging dir so stale files never linger
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Move the ue4ss/ payload up into the staging dir
        for item in inner.iterdir():
            shutil.move(str(item), str(output_path / item.name))

        # Bring the proxy loader (dwmapi.dll) alongside UE4SS.dll
        proxy_src = stage_temp / "dwmapi.dll"
        if not proxy_src.exists():
            logger.error(f"dwmapi.dll not found at zip root ({proxy_src}) — deploy() will fail")
            return False
        shutil.move(str(proxy_src), str(output_path / "dwmapi.dll"))

        # Record the installed version
        try:
            version = (stage_temp / "version.txt").read_text().strip()
            if version:
                version_file.write_text(version)
        except Exception:
            pass

        logger.info(f"UE4SS staged at {output_path}")
        return True
    finally:
        dm.cleanup_temp_files()


def main(force_download: bool = False) -> bool:
    """
    Main function to install all dependencies.

    Args:
        force_download (bool): Force download even if same version exists
    """
    import platform

    logger.info("Installing WRFrontiers-Exporter dependencies...")

    try:
        # Install BatchExport
        logger.info("Installing BatchExport...")
        install_batch_export(force=force_download)

        # Install DepotDownloader
        logger.info("Installing DepotDownloader...")
        install_depot_downloader(force=force_download)

        # Install UE4SS (Linux only — Windows uses Dumper-7 DLL injection)
        if platform.system().lower() == 'linux':
            logger.info("Installing UE4SS (Linux mapper dependency)...")
            install_ue4ss(force=force_download)

        logger.success("All dependencies installed successfully!")

    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

    return True


if __name__ == "__main__":
    main()