"""
Linux-specific .usmap mapper: launches Shipping.exe under umu-run + the
WRF-TLS custom Proton, waits for UE4SS to dump Mappings/*.usmap, then
terminates the game process.

UE4SS loads automatically via the dwmapi.dll proxy (deployed by
ue4ss_deployer.deploy()).  Its USMapAutoStart Lua mod calls
GenerateMappings() after game-state init and then calls os.exit(0),
which collapses the Wine process tree so umu-run exits cleanly.

If umu-run does NOT exit on its own (e.g. the Lua mod doesn't reach
os.exit), we kill the subprocess ourselves once the .usmap file appears
or the timeout expires.

Required env / options (see options_schema.py):
  options.steam_game_download_dir  -- root of the DepotDownloader output
  options.output_mapper_file       -- where to copy the final .usmap
  options.wine_prefix              -- WINEPREFIX path  (Linux only)
  options.proton_path              -- PROTONPATH path  (Linux only)
  options.headless                 -- launch under gamescope's headless backend (no window)
"""
import os
import signal
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from loguru import logger
from optionsconfig import Options

from mapper.ue4ss_deployer import deploy as deploy_ue4ss, get_mappings_dir

# Directory for launcher output logs (repo-root/logs, alongside default.log)
_LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"

# Relative path from steam_game_download_dir to Win64 directory
_WIN64_REL = os.path.join("13_2017027", "WRFrontiers", "Binaries", "Win64")

# How often (seconds) to check for the .usmap output file
_POLL_INTERVAL = 2.0

# Maximum seconds to wait for the dump before giving up
_DUMP_TIMEOUT = 120

# Offscreen render resolution for gamescope's headless backend. The game never
# presents a real frame to a monitor, so the exact size is unimportant — it only
# sizes the offscreen surface the swapchain targets. Kept small to save VRAM.
_GAMESCOPE_W = 1280
_GAMESCOPE_H = 720


def _get_win64_dir(options: Options) -> Path:
    return Path(options.steam_game_download_dir) / _WIN64_REL


def _build_launch_cmd(shipping_exe: Path, headless: bool) -> list:
    """
    Build the launch command for the game.

    Headless wraps ``umu-run`` in gamescope's headless backend
    (``gamescope --backend headless``): gamescope creates an offscreen Vulkan
    swapchain that the NVIDIA driver renders into and exposes a nested display to
    the child, so no window reaches the real desktop and no interactive session is
    required. (Xvfb does not work here — the NVIDIA proprietary driver cannot
    present into its software framebuffer.)

    Raises:
        FileNotFoundError: If HEADLESS is requested but gamescope is not installed.
    """
    umu = ["umu-run", str(shipping_exe)]
    if not headless:
        return umu

    if shutil.which("gamescope") is None:
        raise FileNotFoundError(
            "gamescope is not installed but HEADLESS is enabled. Install it with "
            "'sudo apt-get -t trixie-backports install gamescope', or set "
            "HEADLESS=false to launch on the current DISPLAY."
        )

    return [
        "gamescope", "--backend", "headless",
        "-W", str(_GAMESCOPE_W), "-H", str(_GAMESCOPE_H),
        "-r", "60",
        "--", *umu,
    ]


def _find_usmap(mappings_dir: Path) -> Optional[Path]:
    """Return the first .usmap file found in mappings_dir, or None."""
    if not mappings_dir.is_dir():
        return None
    files = list(mappings_dir.glob("*.usmap"))
    return files[0] if files else None


def _build_env(options: Options) -> dict:
    """Build the env-var dict for the launch.

    When headless, gamescope injects its own nested display into the child game,
    so DISPLAY is left as-is (gamescope reads the ambient one to start its
    headless backend). When not headless, the game inherits the ambient DISPLAY.
    """
    env = os.environ.copy()
    env["WINEPREFIX"] = str(options.wine_prefix)
    env["GAMEID"] = "0"
    env["PROTONPATH"] = str(options.proton_path)
    # Suppress the GCLay/D3D12 crash path (same as routeA-launch.sh).
    # dwmapi=n,b forces Wine to load our dwmapi.dll proxy (which loads UE4SS)
    # instead of Wine's own built-in dwmapi — without this Wine ignores the file.
    env["WINEDLLOVERRIDES"] = "GCLay.dll=d;GCLay64.dll=d;dwmapi=n,b"
    # Signal the Steam Deck hardware path so the game picks ACH 118 routing
    env["SteamDeck"] = "1"
    return env


def main(options: Options) -> str:
    """
    Run the Linux UE4SS mapper pipeline and return the path to the .usmap.

    Steps:
    1. Validate game directory exists.
    2. Deploy UE4SS (idempotent).
    3. Clear any previous Mappings output so we detect a fresh dump.
    4. Launch Shipping.exe under umu-run.
    5. Poll for *.usmap in Mappings/ until it appears or timeout.
    6. Kill umu-run (if still alive).
    7. Copy .usmap to options.output_mapper_file.

    Returns:
        str: Path to the .usmap file at options.output_mapper_file.

    Raises:
        FileNotFoundError: If Shipping.exe or Win64 dir not found.
        TimeoutError: If the .usmap does not appear within _DUMP_TIMEOUT seconds.
        RuntimeError: On any other unrecoverable failure.
    """
    # WINE_PREFIX / PROTON_PATH are optional at the schema level (so they are not
    # required on Windows), so enforce them here for the Linux mapper path.
    missing = [name for name, val in (("WINE_PREFIX", options.wine_prefix),
                                      ("PROTON_PATH", options.proton_path)) if not val]
    if missing:
        raise ValueError(
            f"{', '.join(missing)} must be set for the Linux mapper step. "
            "See the 'Linux setup' section of the README."
        )

    win64_dir = _get_win64_dir(options)
    shipping_exe = win64_dir / "WRFrontiers-Win64-Shipping.exe"

    if not shipping_exe.exists():
        raise FileNotFoundError(
            f"Shipping.exe not found at: {shipping_exe}\n"
            f"Is the game downloaded to {options.steam_game_download_dir}?"
        )

    # 1. Deploy UE4SS (copies DLLs + Lua mod, idempotent)
    logger.info("Deploying UE4SS into Win64 directory...")
    deploy_ue4ss(win64_dir)

    mappings_dir = get_mappings_dir(win64_dir)

    # 2. Clear previous dump output so we don't mistake a stale file for success.
    # NOTE: mappings_dir is the Win64 dir itself (UE4SS writes .usmap there),
    # so only delete stale *.usmap files — never the whole directory.
    for stale in mappings_dir.glob("*.usmap"):
        logger.info(f"Removing stale usmap: {stale.name}")
        stale.unlink()

    # 3. Build the launch command. When headless, this wraps umu-run in
    # gamescope's headless backend so no window reaches the real desktop.
    cmd = _build_launch_cmd(shipping_exe, options.headless)
    if options.headless:
        logger.info("HEADLESS enabled — launching under gamescope --backend headless.")
    else:
        logger.info("HEADLESS disabled — launching on the current DISPLAY.")

    umu_log = None
    try:
        # 4. Launch the game.
        # Tee the launcher's stdout/stderr to a log file rather than an un-drained
        # PIPE: the PIPE is never read during the poll loop, so a chatty game
        # could fill the ~64KB buffer and deadlock, and its output (gamescope/
        # Proton/Wine/vkd3d/Vulkan errors) is exactly what we need when the dump
        # fails.
        env = _build_env(options)
        umu_log_path = _LOGS_DIR / "umu-run.log"
        umu_log_path.parent.mkdir(parents=True, exist_ok=True)
        umu_log = open(umu_log_path, "w")

        logger.info(f"Launching game: {' '.join(cmd)}")
        logger.info(f"  launcher output -> {umu_log_path}")
        logger.debug(f"  DISPLAY={env.get('DISPLAY', '(inherited/unset)')}")
        logger.debug(f"  WINEPREFIX={env['WINEPREFIX']}")
        logger.debug(f"  PROTONPATH={env['PROTONPATH']}")

        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=umu_log,
            stderr=subprocess.STDOUT,
        )
        logger.info(f"launcher PID: {proc.pid}")

        # 5. Poll for .usmap
        usmap_path: Optional[Path] = None
        deadline = time.monotonic() + _DUMP_TIMEOUT
        logger.info(f"Waiting up to {_DUMP_TIMEOUT}s for UE4SS USMAP dump in {mappings_dir}...")

        while time.monotonic() < deadline:
            # Check if the process already exited (os.exit(0) from the Lua mod)
            ret = proc.poll()
            if ret is not None:
                logger.info(f"umu-run exited with code {ret} — checking for dump output...")
                break

            usmap_path = _find_usmap(mappings_dir)
            if usmap_path:
                logger.info(f"USMAP dump detected: {usmap_path}")
                break

            time.sleep(_POLL_INTERVAL)
        else:
            # Timeout: kill and raise
            _terminate_proc(proc)
            raise TimeoutError(
                f"USMAP dump did not appear in {mappings_dir} within {_DUMP_TIMEOUT}s. "
                "Check routeA.log or umu-run output. "
                "Possible causes: UE4SS failed to load, GenerateMappings() not called, "
                "or engine init took longer than expected."
            )

        # Process already exited — do a final scan in case file appeared just before exit
        if usmap_path is None:
            usmap_path = _find_usmap(mappings_dir)

        # Make sure the process is gone even if we broke on ret != None before the file appeared
        _terminate_proc(proc)

        if usmap_path is None:
            raise RuntimeError(
                f"umu-run exited but no .usmap file found in {mappings_dir}. "
                "UE4SS may have loaded but GenerateMappings() may not have completed. "
                "Check umu-run output above."
            )

        # 6. Copy to output location
        out_path = Path(options.output_mapper_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(usmap_path, out_path)
        logger.success(f"USMAP written to: {out_path}")

        return str(out_path)
    finally:
        # Flush/close the launcher log handle. The launch process itself
        # (gamescope, which owns the umu-run/Wine child tree) is terminated on
        # the success, timeout, and error paths above via _terminate_proc(proc).
        if umu_log is not None:
            umu_log.close()


def _terminate_proc(proc: subprocess.Popen) -> None:
    """Terminate umu-run (and its Wine child tree) gracefully then forcefully."""
    if proc.poll() is not None:
        return  # already dead

    logger.info(f"Terminating umu-run (PID {proc.pid})...")
    try:
        # SIGTERM first — lets umu-run clean up the Wine session
        os.kill(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("umu-run did not exit after SIGTERM; sending SIGKILL")
            proc.kill()
            proc.wait(timeout=5)
    except ProcessLookupError:
        pass  # already gone
    logger.debug("umu-run terminated.")
