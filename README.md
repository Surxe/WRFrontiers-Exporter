# WRFrontiers-Exporter

A comprehensive data extraction pipeline for War Robots Frontiers that downloads game files, creates a mapping file, and exports game assets to JSON format.


## Overview

WRFrontiers-Exporter orchestrates a complete 4-step process to extract and convert War Robots Frontiers game data:

1. **Dependency Manager** - Downloads/updates all required dependencies
2. **Steam Download/Update** - Downloads/updates game files via DepotDownloader  
3. **DLL Injection for Mapper** - Creates mapper file via game injection
4. **BatchExport** - Converts game assets to JSON format


## Process Details

### 1. Dependency Manager
- Runs `dependency_manager.py` to download latest release of all dependencies if outdated/missing
- Downloads BatchExport and DepotDownloader tools from their respective GitHub releases
- Automatically checks versions and updates only when necessary

### 2. Steam Download/Update  
- Runs `run_depot_downloader` to download/update the latest War Robots Frontiers game version from Steam
- Download is saved at `STEAM_GAME_DOWNLOAD_DIR`
- Supports downloading specific manifest versions or latest version
- Uses Steam credentials for authentication
- Manifest id (if downloaded latest via `MANIFEST_ID`=`latest`) is saved to `STEAM_GAME_DOWNLOAD_DIR`/manifest.txt

### 3. DLL Injection for Mapper File
- Runs WRF's `Shipping.exe` from the downloaded game files to launch the game without being logged in to Steam
- Injects `src\mapper\Dumper-7.dll` to it to make an SDK
- Extracts the mapper file from the SDK generated in `DUMPER7_OUTPUT_DIR` and copies it to `OUTPUT_MAPPER_FILE`
- May require administrator privileges for DLL injection
- Game cannot be currently open through another source, even through a different steam account

### 4. BatchExport
- Uses the mapper file and steam download
- Exports all `.pak`, `.utoc`, and `.locres` source files to `.json`
- Saves them in `OUTPUT_DATA_DIR`
- Converts game assets to human-readable JSON format


## Installation

1. Clone the repository:
```bash
git clone https://github.com/Surxe/WRFrontiers-Exporter.git
cd WRFrontiers-Exporter
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Copy and configure the environment file:
```bash
cp .env.example .env
# Edit .env with your specific paths and Steam credentials
```

4. Run the exporter:
```bash
python src/run.py --help
```


## Options

### Command Line Argument Usage

For each option, the command line argument may be used at runtime instead of providing it in the `.env`.

```bash
python src/run.py                       # Run all steps with default/env values
python src/run.py --log-level INFO      # Run all steps with default/env values, except with LOG_LEVEL INFO
```

### Parameters

Copy `.env.example` to `.env` and configure the following parameters, unless they will be provided as arguments at runtime:

<!-- BEGIN_GENERATED_OPTIONS -->
#### Logging

* **LOG_LEVEL** - Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
  - Default: `"DEBUG"`
  - Command line: `--log-level`


#### Dependencies

* **SHOULD_DOWNLOAD_DEPENDENCIES** - Whether to download dependencies.
  - Default: `"false"`
  - Command line: `--should-download-dependencies`

* **FORCE_DOWNLOAD_DEPENDENCIES** - Re-download dependencies even if they are already present.
  - Default: `"false"`
  - Command line: `--force-download-dependencies`
  - Depends on: `SHOULD_DOWNLOAD_DEPENDENCIES`


#### Steam Download

* **SHOULD_DOWNLOAD_STEAM_GAME** - Whether to download Steam game files.
  - Default: `"false"`
  - Command line: `--should-download-steam-game`

* **FORCE_STEAM_DOWNLOAD** - Re-download/update Steam game files even if they are already present.
  - Default: `"false"`
  - Command line: `--force-steam-download`
  - Depends on: `SHOULD_DOWNLOAD_STEAM_GAME`

* **MANIFEST_ID** - Steam manifest ID to download. If 'latest', the latest manifest ID will be used.
  - Default: `"latest"`
  - Command line: `--manifest-id`
  - Depends on: `SHOULD_DOWNLOAD_STEAM_GAME`
  - [SteamDB](https://steamdb.info/app/1491000/depot/1491005/manifests/)

* **STEAM_USERNAME** - Steam username for authentication.
  - Example: `"example_user"`
  - Default: None - required when SHOULD_DOWNLOAD_STEAM_GAME is True
  - Command line: `--steam-username`
  - Depends on: `SHOULD_DOWNLOAD_STEAM_GAME`

* **STEAM_PASSWORD** - Steam password for authentication.
  - Example: `"example_password"`
  - Default: None - required when SHOULD_DOWNLOAD_STEAM_GAME is True
  - Command line: `--steam-password`
  - Depends on: `SHOULD_DOWNLOAD_STEAM_GAME`

* **STEAM_GAME_DOWNLOAD_DIR** - Path to the local Steam game installation directory.
  - Example: `"C:/WRFrontiersDB/SteamDownload"`
  - Default: None - required when SHOULD_DOWNLOAD_STEAM_GAME is True
  - Command line: `--steam-game-download-dir`
  - Depends on: `SHOULD_DOWNLOAD_STEAM_GAME`


#### Mapping

* **SHOULD_GET_MAPPER** - Whether to get the mapping file using Dumper7.
  - Default: `"false"`
  - Command line: `--should-get-mapper`

* **FORCE_GET_MAPPER** - Re-generate the mapping file even if it already exists.
  - Default: `"false"`
  - Command line: `--force-get-mapper`
  - Depends on: `SHOULD_GET_MAPPER`

* **DUMPER7_OUTPUT_DIR** - Path to the where Dumper7 outputs its generated SDK.
  - Example: `"C:/Dumper-7"`
  - Default: None - required when SHOULD_GET_MAPPER is True
  - Command line: `--dumper7-output-dir`
  - Depends on: `SHOULD_GET_MAPPER`
  - If unsure where this is, it is likely `C:/Dumper-7`. Confirm by running the mapper, letting it fail, and checking for the dir.

* **OUTPUT_MAPPER_FILE** - Path to save the generated mapping file (.usmap) at. Should end in .usmap
  - Example: `"C:/WRFrontiersDB/Mappings/2025-09-30.usmap"`
  - Default: None - required when SHOULD_GET_MAPPER or SHOULD_BATCH_EXPORT is True
  - Command line: `--output-mapper-file`
  - Depends on: `SHOULD_GET_MAPPER`, `SHOULD_BATCH_EXPORT`


#### Batch Export

* **SHOULD_BATCH_EXPORT** - Whether to run the BatchExport tool to export assets.
  - Default: `"false"`
  - Command line: `--should-batch-export`

* **FORCE_EXPORT** - Re-run the BatchExport even if output directory is not empty.
  - Default: `"false"`
  - Command line: `--force-export`
  - Depends on: `SHOULD_BATCH_EXPORT`

* **OUTPUT_DATA_DIR** - Path to save the exported assets to.
  - Example: `"C:/WRFrontiersDB/ExportedData"`
  - Default: None - required when SHOULD_BATCH_EXPORT is True
  - Command line: `--output-data-dir`
  - Depends on: `SHOULD_BATCH_EXPORT`

* **SHOULD_EXPORT_TEXTURES** - Whether to export textures.
  - Default: `"true"`
  - Command line: `--should-export-textures`
  - Depends on: `SHOULD_BATCH_EXPORT`


<!-- END_GENERATED_OPTIONS -->
### Miscellaneous Option Behavior

* An option's value is determined by the following priority, in descending order
  * Argument
  * Option
  * Default
* If all options prefixed with `SHOULD_` are defaulted to `False`, they are instead all defaulted to `True` for ease of use
* Options are only required if their section's root `SHOULD_` option is `True`


## Requirements

- Python 3.7+
- Administrator privileges (optimal for DLL injection)
- Steam account credentials
- Windows OS (for game execution and DLL injection)


## Troubleshooting

### Common Issues

1. **DLL Injection Fails**
   - Ensure you're running as Administrator
   - Check that the game executable path is correct
   - Verify Dumper-7 dir exists in the mapper directory

2. **Steam Authentication Fails**
   - Verify your Steam username and password are correct
   - Check that Steam Guard is not blocking the login
   - Ensure DepotDownloader has the latest version

3. **Path Not Found Errors**
   - Verify all directory paths exist and are accessible
   - Use forward slashes (/) in paths for compatibility
   - Ensure parent directories exist for output paths

4. **Permission Errors**
   - Run the script as Administrator
   - Check that output directories are writable
   - Verify antivirus isn't blocking file operations


## Contributing

* After making changes to `options_schema.py`, rerun `build/docs.py` to rebuild the `.env.example` and `README.md`
* Follow standards set by `STANDARDS.md`


## Disclaimer

This tool is for educational and research purposes. Ensure you comply with the terms of service of War Robots Frontiers and Steam when using this software.
