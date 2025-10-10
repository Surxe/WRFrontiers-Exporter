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
