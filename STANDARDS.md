# Standards

## Case
snake_case

## Path variable naming
* Folder -> `dir`
* File
  * Executable File -> `cmd`
  * Other File -> `file`

## Terminology
### Settings / Options
* Argument - CLI provided variable at runtime, i.e. `--log-level`
* Parameter / Environment Variable - `.env` provided variable, i.e. `LOG_LEVEL`
* Default: Default value for a given option
* Option - Argument, or option, or default (in descending order of priority)
* todo: update workspace to use Option instead of option in these places