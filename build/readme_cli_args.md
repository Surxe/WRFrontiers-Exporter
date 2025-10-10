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
