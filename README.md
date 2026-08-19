# WRFrontiers-Exporter

A comprehensive data extraction pipeline for War Robots Frontiers that downloads game files, creates a mapping file, and exports game assets to JSON format.


## Overview

WRFrontiers-Exporter orchestrates a complete 4-step process to extract and convert War Robots Frontiers game data:

1. **Dependency Manager** - Downloads/updates all required dependencies
2. **Steam Download/Update** - Downloads/updates game files via DepotDownloader  
3. **Mapper Generation** - Creates the `.usmap` mapping file by launching the game
4. **BatchExport** - Converts game assets to JSON format

### Platform support

The pipeline runs on both **Windows** and **Linux**. The only step that differs
between them is step 3 (mapper generation), because War Robots Frontiers is a
Windows game with no native Linux build:

| Step | Windows | Linux |
| --- | --- | --- |
| 1. Dependencies | BatchExport + DepotDownloader (windows-x64) | + UE4SS, Linux Oodle, Detex (built from source) |
| 2. Steam download | DepotDownloader (windows-x64) | DepotDownloader (linux-x64, native ELF) |
| 3. Mapper | Dumper-7 DLL injection into `Shipping.exe` | UE4SS loaded via `dwmapi.dll` proxy, game run under Proton via `umu-run` |
| 4. BatchExport | `BatchExport.exe` | `BatchExport` (native ELF) |

The exporter auto-detects the OS and selects the correct tools; you use the same
`src/run.py` command either way. Linux has extra one-time host setup — see
[Linux setup](#linux-setup).


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

### 3. Mapper Generation
Launches WRF's `Shipping.exe` from the downloaded game files (without being
logged in to Steam) long enough to generate the `.usmap` mapping file, then
copies it to `OUTPUT_MAPPER_FILE`. The mechanism is OS-specific:

**Windows** (`SimpleDLLInjector`):
- Injects `src\mapper\Dumper-7.dll` into the running game to build an SDK
- Extracts the mapper from the SDK generated in `DUMPER7_OUTPUT_DIR`
- May require administrator privileges for DLL injection
- The game cannot already be open through another source (even a different Steam account)

**Linux** (`linux_mapper` + UE4SS):
- Deploys UE4SS into the game's `Win64` directory (`dwmapi.dll` proxy + `UE4SS.dll`)
  along with a small `USMapAutoStart` Lua mod that calls UE4SS's built-in
  `DumpUSMAP()` and then exits
- Launches `Shipping.exe` under the custom WRF-TLS Proton build via `umu-run`,
  by default wrapped in gamescope's headless backend (`gamescope --backend
  headless`) so no window appears on screen and
  no interactive desktop session is required (set `HEADLESS=false` to launch on
  the real display instead)
- Waits for UE4SS to write the `.usmap`, then terminates the game
- Requires the one-time [Linux setup](#linux-setup) (umu-launcher + custom Proton
  + gamescope)

### 4. BatchExport
- Uses the mapper file and steam download
- Exports all `.pak`, `.utoc`, and `.locres` source files to `.json`
- Saves them in `OUTPUT_DATA_DIR`
- Converts game assets to human-readable JSON format
- On Linux, uses a native ELF build of BatchExport plus Linux Oodle and Detex
  libraries that the dependency step installs automatically


## Installation

These steps are the same on Windows and Linux. **Linux users must also complete
the one-time [Linux setup](#linux-setup) below** before the mapper step (3) will
work.

1. Clone the repository:
```bash
git clone https://github.com/Surxe/WRFrontiers-Exporter.git
cd WRFrontiers-Exporter
```

2. Create a virtual environment and install Python dependencies:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
```

3. Copy and configure the environment file:
```bash
cp .env.example .env
# Edit .env with your specific paths and Steam credentials.
# Linux: also set WINE_PREFIX and PROTON_PATH (see Linux setup).
```

4. Run the exporter:
```bash
python src/run.py --help
```

On the first real run, enable the dependency step so the tools are downloaded
(and, on Linux, the native libraries are built/installed):
```bash
python src/run.py --should-download-dependencies true
```


## Linux setup

War Robots Frontiers has no native Linux build, so the mapper step (3) launches
the Windows `Shipping.exe` under a custom Proton build via
[umu-launcher](https://github.com/Open-Wine-Components/umu-launcher). This is a
one-time host setup, separate from the exporter itself.

### Prerequisites

Install these system packages (names shown for Debian/Ubuntu; adjust for your
distro):

- **Python 3.8+** with `venv` — `python3 python3-venv`
- **git** and a **C toolchain** — `git gcc` — the dependency step builds the
  Linux Detex texture library from source (`hglm/detex`). If `gcc`/`git` are
  missing the build is skipped with a warning; data/JSON export still works, but
  texture decoding will not.
- **umu-launcher** — install from the
  [umu-launcher releases](https://github.com/Open-Wine-Components/umu-launcher/releases)
  (a `.deb` is provided for Debian/Ubuntu; other distros have their own
  packages). Verify with `umu-run --version`.
- **gamescope** — `gamescope` — provides the headless display the mapper step
  renders into when `HEADLESS` is enabled (the default). gamescope creates an
  offscreen Vulkan swapchain the GPU renders into, so only the on-screen window is
  suppressed. On Debian it lives in `trixie-backports/contrib`, so install with
  `sudo apt-get -t trixie-backports install gamescope`. Set `HEADLESS=false` to
  launch on your real `DISPLAY` instead (useful for watching the launch while
  debugging), in which case gamescope is not needed.
  (Note: plain `Xvfb` does **not** work with the NVIDIA proprietary driver — it
  cannot present into Xvfb's software framebuffer — which is why gamescope's
  headless backend is used.)
- **A working GPU.** The mapper step launches the game under Proton to let UE4SS
  dump the `.usmap`. With `HEADLESS` enabled it runs under gamescope's headless
  backend with no visible window and no interactive desktop session required; with
  `HEADLESS=false` it opens the game window on your current display for a few
  seconds.

The exporter's Linux-only dependencies (UE4SS, the Linux Oodle library, and the
Detex build) are all handled automatically by the dependency step
(`--should-download-dependencies true`) — you do not install them by hand.

### Custom Proton (WRF-TLS build)

The game only launches far enough to dump the mapper with the patched Proton
build from [OwendB1/WRF-Compat-Tools](https://github.com/OwendB1/WRF-Compat-Tools).

```bash
git clone https://github.com/OwendB1/WRF-Compat-Tools.git
cd WRF-Compat-Tools
# Extract the custom Proton into a directory of your choice:
./Steam/setup.sh --target /path/to/proton
```

This produces `/path/to/proton/GE-Proton10-34-WRF-TLS`. Point the exporter at it
via `.env`:

```bash
# Absolute path to the extracted custom Proton build
PROTON_PATH="/path/to/proton/GE-Proton10-34-WRF-TLS"
# A writable directory for the Wine prefix (created on first launch)
WINE_PREFIX="/path/to/wrf/prefix"
```

You do **not** need the Steam client for the mapper step — `umu-run` launches
`Shipping.exe` directly. The exporter sets the required Wine env internally
(`WINEDLLOVERRIDES=...;dwmapi=n,b`, `SteamDeck=1`).

### Run

With the prerequisites in place and `.env` filled in, run the full pipeline as
usual:

```bash
python src/run.py --should-download-dependencies true \
                  --should-download-steam-game true \
                  --should-get-mapper true \
                  --should-batch-export true
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

* **DUMPER7_OUTPUT_DIR** - (Windows only) Path to where Dumper7 outputs its generated SDK. Not required on Linux — the UE4SS path is used instead.
  - Example: `"C:/Dumper-7"`
  - Default: None
  - Command line: `--dumper7-output-dir`
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


#### Mapping (Linux)

* **WINE_PREFIX** - (Linux only) Path to the Wine prefix directory (WINEPREFIX). Required for the mapper step on Linux; unused on Windows. Validated at runtime rather than via depends_on so it is not required on Windows.
  - Example: `"/srv/dev/wrf/prefix"`
  - Default: None
  - Command line: `--wine-prefix`

* **PROTON_PATH** - (Linux only) Path to the Proton installation directory (PROTONPATH). Must be the WRF-TLS custom build. Required for the mapper step on Linux; unused on Windows. Validated at runtime rather than via depends_on so it is not required on Windows.
  - Example: `"/srv/dev/wrf/proton/GE-Proton10-34-WRF-TLS"`
  - Default: None
  - Command line: `--proton-path`

* **HEADLESS** - (Linux only) Launch the game under gamescope's headless backend ('gamescope --backend headless') during the mapper step so no window appears on screen and no interactive desktop session is required. The GPU still renders offscreen; only the visible window is suppressed. Requires the 'gamescope' package. Ignored on Windows. Set to false to launch on the current DISPLAY (useful for debugging the launch visually).
  - Default: `"true"`
  - Command line: `--headless`


<!-- END_GENERATED_OPTIONS -->
### Miscellaneous Option Behavior

* An option's value is determined by the following priority, in descending order
  * Argument
  * Option
  * Default
* If all options prefixed with `SHOULD_` are defaulted to `False`, they are instead all defaulted to `True` for ease of use
* Options are only required if their section's root `SHOULD_` option is `True`


## Requirements

Common:
- Python 3.8+
- Steam account credentials

Windows:
- Windows OS (for game execution and DLL injection)
- Administrator privileges (optimal for DLL injection)

Linux:
- umu-launcher and the WRF-TLS custom Proton build (see [Linux setup](#linux-setup))
- `git` + a C toolchain (`gcc`) for the Detex build (optional; only needed for
  texture decoding)
- gamescope, for the default headless mapper launch (see [Linux setup](#linux-setup))
- A working GPU (with `HEADLESS` the mapper runs offscreen with no window; with
  `HEADLESS=false` it briefly opens the game on your current display)


## Troubleshooting

### Common Issues

1. **DLL Injection Fails (Windows)**
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
   - Run the script as Administrator (Windows)
   - Check that output directories are writable
   - Verify antivirus isn't blocking file operations

### Linux-specific Issues

Check the UE4SS log at `<Win64>/UE4SS.log` inside the Steam download for mapper
problems (`<Win64>` = `<STEAM_GAME_DOWNLOAD_DIR>/13_2017027/WRFrontiers/Binaries/Win64`).

1. **Mapper times out / no `.usmap` produced**
   - `umu-run` not installed or not on `PATH` — verify with `umu-run --version`
   - `PROTON_PATH` doesn't point at the extracted `GE-Proton10-34-WRF-TLS` dir
   - No display/GPU available — the game must be able to open a window. Run from
     a graphical session, not a bare SSH shell.
   - UE4SS log shows `PS scan timed out` / `Failed to find FText::FText` — the
     game updated and the bundled AOB no longer matches; the
     `FText_Constructor.lua` signature in `src/mapper/ue4ss_deployer.py` needs
     re-deriving.
   - UE4SS log shows `Engine version is not supported` — the pinned UE4SS
     `experimental-latest` build predates the game's engine version; update it.

2. **BatchExport crashes at "Initializing Oodle/Detex"**
   - The Linux native libraries are missing — re-run with
     `--should-download-dependencies true --force-download-dependencies true`
   - Detex specifically requires `gcc` + `git` at install time to build from
     source; install them and re-run the dependency step. Without Detex, run with
     `--should-export-textures false` to skip texture decoding.

3. **`DllNotFoundException` for `oodle-data-shared.dll` / `Detex.dll`**
   - These are loaded by bare name via `dlopen`; the exporter adds the
     BatchExport directory to `LD_LIBRARY_PATH` automatically. If you invoke
     BatchExport manually, set `LD_LIBRARY_PATH` to its directory yourself.


## Contributing

* After making changes to `options_schema.py`, rerun `build/docs.py` to rebuild the `.env.example` and `README.md`
* Follow standards set by `STANDARDS.md`


## Disclaimer

This tool is for educational and research purposes. Ensure you comply with the terms of service of War Robots Frontiers and Steam when using this software.
