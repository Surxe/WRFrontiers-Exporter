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
- Download is saved at `STEAM_GAME_DOWNLOAD_PATH`
- Supports downloading specific manifest versions or latest version
- Uses Steam credentials for authentication

### 3. DLL Injection for Mapper File
- Runs WRF's `Shipping.exe` from the downloaded game files to launch the game without being logged in to Steam
- Injects `src\mapper\Dumper-7.dll` to it to make an SDK
- Extracts the mapper file from the SDK generated in `DUMPER7_OUTPUT_DIR` and copies it to `OUTPUT_MAPPER_FILE`
- May require administrator privileges for DLL injection

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
python src/run.py
```

<!-- BEGIN_GENERATED_PARAMS -->
## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following parameters:

#### Logging

- **LOG_LEVEL** - Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
  - Default: `"DEBUG"`
  - Command line: `--log-level`

#### Dependencies

- **SHOULD_DOWNLOAD_DEPENDENCIES** - Whether to download dependencies.
  - Default: `"true"`
  - Command line: `--should-download-dependencies`

* **FORCE_DOWNLOAD_DEPENDENCIES** - Re-download dependencies even if they are already present.
  - Default: `"false"`
  - Command line: `--force-download-dependencies`

#### Steam Download

- **SHOULD_DOWNLOAD_STEAM_GAME** - Whether to download Steam game files.
  - Default: `"true"`
  - Command line: `--should-download-steam-game`

* **FORCE_STEAM_DOWNLOAD** - Re-download/update Steam game files even if they are already present.
  - Default: `"false"`
  - Command line: `--force-steam-download`

* **MANIFEST_ID** - Steam manifest ID to download. If blank, the latest manifest ID will be used.
  - Default: `""` (empty for latest)
  - Command line: `--manifest-id`
  - See [SteamDB](https://steamdb.info/app/1491000/depot/1491005/manifests/) for available values

* **STEAM_USERNAME** - Steam username for authentication.
  - Default: None
  - Command line: `--steam-username`

* **STEAM_PASSWORD** - Steam password for authentication.
  - Default: None
  - Command line: `--steam-password`

* **STEAM_GAME_DOWNLOAD_PATH** - Path to the local Steam game installation directory.
  - Default: None
  - Command line: `--steam-game-download-path`

#### Mapping

- **SHOULD_GET_MAPPER** - Whether to get the mapping file using Dumper7.
  - Default: `"true"`
  - Command line: `--should-get-mapper`

* **FORCE_GET_MAPPER** - Re-generate the mapping file even if it already exists.
  - Default: `"true"`
  - Command line: `--force-get-mapper`

* **DUMPER7_OUTPUT_DIR** - Path to the where Dumper7 outputs its generated SDK.
  - Default: None
  - Command line: `--dumper7-output-dir`
  - If unsure where this is, it is likely C:/Dumper-7. Confirm by running the mapper, letting it fail, and checking for the dir.

* **OUTPUT_MAPPER_FILE** - Path to save the generated mapping file (.usmap) at. Should end in .usmap
  - Default: None
  - Command line: `--output-mapper-file`

#### Batch Export

- **SHOULD_BATCH_EXPORT** - Whether to run the BatchExport tool to export assets.
  - Default: `"true"`
  - Command line: `--should-batch-export`

* **FORCE_EXPORT** - Re-run the BatchExport even if output directory is not empty.
  - Default: `"true"`
  - Command line: `--force-export`

* **OUTPUT_DATA_DIR** - Path to save the exported assets to.
  - Default: None
  - Command line: `--output-data-dir`

## Command Line Arguments

All environment variables can be overridden via command line arguments.

### Configuration Parameters
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}` - Logging level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- `--manifest-id MANIFEST_ID` - Steam manifest ID to download. If blank, the latest manifest ID will be used.
- `--steam-username STEAM_USERNAME` - Steam username for authentication.
- `--steam-password STEAM_PASSWORD` - Steam password for authentication.
- `--steam-game-download-path STEAM_GAME_DOWNLOAD_PATH` - Path to the local Steam game installation directory.
- `--dumper7-output-dir DUMPER7_OUTPUT_DIR` - Path to the where Dumper7 outputs its generated SDK.
- `--output-mapper-file OUTPUT_MAPPER_FILE` - Path to save the generated mapping file (.usmap) at. Should end in .usmap
- `--output-data-dir OUTPUT_DATA_DIR` - Path to save the exported assets to.

### Force Options
- `--force-download-dependencies` - Re-download dependencies even if they are already present.
- `--force-steam-download` - Re-download/update Steam game files even if they are already present.
- `--force-get-mapper` - Re-generate the mapping file even if it already exists.
- `--force-export` - Re-run the BatchExport even if output directory is not empty.

### Control Options
- `--should-download-dependencies` - Whether to download dependencies.
- `--should-download-steam-game` - Whether to download Steam game files.
- `--should-get-mapper` - Whether to get the mapping file using Dumper7.
- `--should-batch-export` - Whether to run the BatchExport tool to export assets.

<!-- END_GENERATED_PARAMS -->

## Command Line Usage

### Basic Usage
```bash
python src/run.py                           # Run all steps with default/env values
```

### Parameter Override Examples
```bash
python src/run.py --log-level INFO          # Set log level
python src/run.py --manifest-id 1234567890 --force-steam-download   # Download specific manifest version
python src/run.py --steam-username user --steam-password pass       # Override Steam credentials
python src/run.py --force-download-dependencies --force-export      # Force all downloads and exports
```

### Skip Specific Steps
```bash
python src/run.py --skip-dependencies      # Skip dependency check/update
python src/run.py --skip-steam-update      # Skip steam game download/update
python src/run.py --skip-mapper            # Skip mapper file creation
python src/run.py --skip-batch-export      # Skip batch export to JSON
```

### Run Only Specific Steps
```bash
python src/run.py --skip-dependencies --skip-steam-update    # Only mapper + export
python src/run.py --skip-mapper --skip-batch-export          # Only deps + steam
```

## Requirements

- Python 3.7+
- Administrator privileges (optimal for DLL injection)
- Steam account credentials
- Windows OS (for game execution and DLL injection)

## Directory Structure

```
WRFrontiers-Exporter/
├── src/
│   ├── run.py                    # Main orchestration script
│   ├── utils.py                  # Shared utilities and parameter management
│   ├── dependency_manager.py     # Dependency download/update management
│   ├── steam/
│   │   └── run_depot_downloader.py  # Steam game download
│   ├── mapper/
│   │   ├── get_mapper.py         # DLL injection and mapper creation
│   │   ├── simple_injector.py   # DLL injection utilities
│   │   └── Dumper-7.dll         # UE4 SDK generation DLL
│   └── cue4p-batchexport/
│       └── run_batch_export.py  # Asset export to JSON
├── logs/                         # Log files
├── .env.example                  # Environment configuration template
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

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

### Debug Mode

Run with debug logging for detailed troubleshooting:
```bash
python src/run.py --log-level DEBUG
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Disclaimer

This tool is for educational and research purposes. Ensure you comply with the terms of service of War Robots Frontiers and Steam when using this software.
