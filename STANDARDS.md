# Standards

## Code Conventions

### Case
- **snake_case** - Used for variables and functions
- **PascalCase** - Used for class names (e.g., `DependencyManager`, `ArgumentWriter`, `Options`)
- ***CREAMING_SNAKE_CASE** - Used for schema keys and environment variables (e.g., `LOG_LEVEL`, `STEAM_USERNAME`)

### Path Variable Naming
* **Folder Path** → `dir` (e.g., `output_dir`, `steam_dir`, `logs_dir`)
* **File Path**
  * **Executable File** → `cmd` (e.g., `depot_downloader_cmd`)
  * **Other File** → `file` (e.g., `log_file`, `mapper_file`, `version_file`)

### Function/Method Naming
* **Private methods** - Methods that use (not just have) `self` arg. Prefixed with `_` (e.g., `_process_schema`, `_download_file`, `_validate_zip_file`)

### File Extensions & Types
* **Configuration files** - `.json` (e.g., `appsettings.template.json`)
* **Log files** - `.log` (e.g., `latest.log`, `output.log`, `default.log`)
* **Version files** - `version.txt`
* **Mapper files** - `.usmap` (Unreal mapping files)
* **Executables** - `.exe` (Windows executables)
* **DLL files** - `.dll` (Dynamic link libraries)
  
## File & Directory Structure

### Case
* **Installation directories** - PascalCase (e.g., `BatchExport/`, `DepotDownlader/`)
* **Documentation files** - ALLCAPSNOSPACE (e.g., `README.md`, `STANDARDS.md`)
* **Other directories/files** - snake_case (e.g., `cue4p_batchexport/`, `build_scripts/`, `steam/`, `run_batch_export.py`)

### Patterns
* **Installation wrappers** - prefixed with `run_` (e.g., `run_depot_downloader.py`)

## Terminology

### Settings / Options
* **Argument** - CLI provided variable at runtime, i.e. `--log-level`
* **Parameter / Environment Variable** - `.env` provided variable, i.e. `LOG_LEVEL`
* **Default** - Default value for a given option
* **Option** - Argument, parameter, or default (in descending order of priority)
* **Root Option** - An option that has sub-options via `section_options` (e.g., `SHOULD_DOWNLOAD_STEAM_GAME`)
* **Section Option** - A sub-option of the section's root option (e.g., `STEAM_USERNAME` under `SHOULD_DOWNLOAD_STEAM_GAME`)

### Process Management
* **Process** - Running executable/application instance
* **PID** - Process ID for system identification
* **Injection** - DLL injection into running process for modification
* **Manifest ID** - Steam depot version identifier
* **Timeout** - Maximum wait time for process operations

### Dependencies & Tools
* **DepotDownloader** - Steam content downloading tool
* **BatchExport** - Game asset export utility (CUE4P-BatchExport)
* **Dumper-7** - Unreal Engine SDK generation DLL
* **Mapper / Mapping File** - Unreal Engine object mapping file (.usmap)

### Logging Standards
* **Log Levels** - `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
* **Sensitive Data** - Password fields masked with `***HIDDEN***`
* **Process Logging** - Format: `[process: {name}] {message}`
* **Timer Logging** - Include start/end timestamps and elapsed time

## Testing Conventions

### Test File Structure
* **Test files** - `test_{module_name}.py`
* **Test classes** - `Test{ClassName}` (e.g., `TestOptions`, `TestDependencyManager`)
* **Test methods** - `test_{functionality}_{scenario}` (e.g., `test_options_init_with_args`)

### Test Organization
* **setUp/tearDown** - Use for test preparation and cleanup
* **Mock objects** - Prefix with `mock_` (e.g., `mock_logger`, `mock_subprocess`)
* **Temporary directories** - Create in `setUp`, clean in `tearDown`
* **Assertions** - Use descriptive assertion methods