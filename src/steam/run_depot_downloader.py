import os
import shutil
from loguru import logger
from utils import run_process, init_params, Params

APP_ID = '1491000'  # war robots: frontier's app_id
DEPOT_ID = '1491005'  # the big depot


class DepotDownloader:
    def __init__(self, wrf_dir, steam_username, steam_password, force):
        self.depot_downloader_cmd_path = 'src/steam/DepotDownloader/DepotDownloader.exe'
        if not os.path.exists(self.depot_downloader_cmd_path):
            raise Exception('Is DepotDownloader installed? Run dependency_manager.py')
        if not steam_username or not steam_password:
            raise Exception('Steam username and password are required')

        self.app_id = APP_ID
        self.depot_id = DEPOT_ID

        self.steam_username = steam_username
        self.steam_password = steam_password
        self.wrf_dir = wrf_dir
        self.manifest_path = os.path.join(self.wrf_dir, 'manifest.txt')
        self.force = force

    def run(self, manifest_id):
        # no input manifest id downloads the latest version
        if manifest_id is None:
            manifest_id = self._get_latest_manifest_id()
            logger.debug(f"DepotDownloader retrieved latest manifest id of: {manifest_id}")

        # Check if the manifest is already downloaded
        downloaded_manifest_id = self._read_downloaded_manifest_id()
        if downloaded_manifest_id == manifest_id and not self.force:
            logger.info(f'Already downloaded manifest {manifest_id}')
            return

        self._download(manifest_id)
        self._write_downloaded_manifest_id(manifest_id)

    def _download(self, manifest_id):
        logger.debug(f'Downloading game with manifest id {manifest_id}')

        subprocess_params = [
            os.path.join(self.depot_downloader_cmd_path),
            '-app', self.app_id,
            '-depot', self.depot_id,
            '-manifest', manifest_id,
            '-username', self.steam_username,
            '-password', self.steam_password,
            '-remember-password',
            '-dir', self.wrf_dir,
        ]
        run_process(subprocess_params, name='download-game-files')

        # todo, verify files are downloaded

    def _read_downloaded_manifest_id(self):
        if not os.path.exists(self.manifest_path):
            return None

        with open(self.manifest_path, 'r') as f:
            manifest_id = f.read().strip()
        return manifest_id

    def _get_latest_manifest_id(self):
        # create temporary folder to store manifest file
        temp_dir = os.path.join(self.wrf_dir, 'temp')

        subprocess_params = [
            os.path.join(self.depot_downloader_cmd_path),
            '-app',
            self.app_id,
            '-depot',
            self.depot_id,
            '-username',
            self.steam_username,
            '-password',
            self.steam_password,
            '-remember-password',
            '-dir',
            temp_dir,
            '-manifest-only',
            '-validate',
        ]
        run_process(subprocess_params, name='get-latest-manifest-id')

        manifest_id = None
        for filename in os.listdir(temp_dir):
            if filename.startswith('manifest'):
                # manifest formatted as manifest_<depot_id>_<manifest_id>.txt
                manifest_id = filename.replace('manifest_', '').replace('.txt', '').split('_')[-1]

        shutil.rmtree(temp_dir)
        return manifest_id

    def _write_downloaded_manifest_id(self, manifest_id):
        logger.debug('Writing manifest id', manifest_id, 'to', self.manifest_path)
        with open(self.manifest_path, 'w') as f:
            f.write(manifest_id)

if __name__ == '__main__':
    params = init_params()

    if params is None:
        raise ValueError("Params must be provided")
    
    DepotDownloader(
        wrf_dir=params.steam_game_download_path,
        steam_username=params.steam_username,
        steam_password=params.steam_password,
        force=params.force_steam_download,
    ).run(manifest_id=params.manifest_id)