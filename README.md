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

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following parameters:

#### Logging
- **LOG_LEVEL** - Set the log level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Default: `"DEBUG"`

#### Dependencies  
- **FORCE_DOWNLOAD_DEPENDENCIES** - Set to `"True"` to force re-download of dependencies even if they are the same version. Set to `"False"` to skip downloading if the version matches.
  - Default: `"False"`

#### Steam Download
- **MANIFEST_ID** - Specific Steam manifest ID to download. Leave empty to download the latest version. Use specific ID to download a particular game version. See [SteamDB](https://steamdb.info/depot/1491005/manifests) for list of manifest id's for WRF.
  - Default: `""` (empty for latest)
- **FORCE_STEAM_DOWNLOAD** - Set to `"True"` to force re-download of the latest manifest even if the previously installed manifest id is the same. If true and a previous installation is here, it will simply update the installation.
  - Default: `"False"`
- **STEAM_USERNAME** - Your Steam username for DepotDownloader authentication.
- **STEAM_PASSWORD** - Your Steam password for DepotDownloader authentication.
- **STEAM_GAME_DOWNLOAD_PATH** - Path where the game will be downloaded by DepotDownloader. Ensure it exists. A prior version can exist here if not corrupted and it will be updated to latest version.
  - Example: `"C:/WRFrontiersDB/SteamDownload"`

#### Mapper Creation
- **DUMPER7_OUTPUT_DIR** - Path to Dumper-7's output folder. If you're not sure where this path is for you, it is likely this default path. You can confirm by running `src/mapper/get_mapper.py`, letting it error, then looking for the directory. Ensure it exists. Content will be cleared before mapper is created so that the created mapper can be located properly.
  - Default: `"C:/Dumper-7"`
- **OUTPUT_MAPPER_FILE** - Where the generated mapper file will be saved as. Ensure the parent dirs exists.
  - Example: `"C:/WRFrontiersDB/mapper.usmap"`
- **FORCE_GET_MAPPER** - If true and a previous mapper is here, it will be overwritten. Set to `"False"` to skip mapper creation if the file already exists.
  - Default: `"True"`

#### Export Output
- **OUTPUT_DATA_DIR** - Path to where the output JSON will be saved. This should point to the "WRFrontiers\Content" folder that contains all json files of the game. Ensure the parent dirs exists. When using BatchExport, it will wipe its contents before generating these files.
  - Example: `"C:/WRFrontiersDB/ExportData"`
- **FORCE_EXPORT** - If true and a previous export is here, it will be overwritten. Set to `"False"` to skip exporting if the folder already exists.
  - Default: `"True"`

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

## Command Line Arguments

### Configuration Parameters
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}` - Set the log level
- `--manifest-id MANIFEST_ID` - Specific Steam manifest ID to download (leave empty for latest)
- `--steam-username USERNAME` - Steam username for DepotDownloader authentication
- `--steam-password PASSWORD` - Steam password for DepotDownloader authentication
- `--steam-game-download-path PATH` - Path where the game will be downloaded by DepotDownloader
- `--dumper7-output-dir PATH` - Path to Dumper-7's output folder
- `--output-mapper-file PATH` - Where the generated mapper file will be saved
- `--output-data-dir PATH` - Path where the output JSON will be saved

### Force Options
- `--force-download-dependencies` - Force re-download of dependencies even if same version exists
- `--force-steam-download` - Force re-download of Steam files even if same manifest exists
- `--force-get-mapper` - Force regeneration of mapper file even if it exists
- `--force-export` - Force re-export of game data even if output exists

### Skip Options
- `--skip-dependencies` - Skip dependency manager step
- `--skip-steam-update` - Skip steam download/update step
- `--skip-mapper` - Skip mapper creation step
- `--skip-batch-export` - Skip batch export step

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
