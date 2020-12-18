import requests
import subprocess
from credentials import *


def main():
    # Check if qBittorrent daemon is currently running
    check_qbt = subprocess.run('systemctl is-active qbittorrent', \
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)
    if check_qbt.returncode == 0:
        r_auth = requests.post('http://localhost:8080/api/v2/auth/login', \
                 headers={'Referer': 'http://localhost:8080'}, \
                 data={'username': qbtusername, 'password': qbtpassword}, timeout=27.05)
        r_get = requests.get('http://localhost:8080/api/v2/torrents/info?filter=completed&sort=completion_on', \
                cookies=r_auth.cookies.get_dict(), timeout=27.05)
    else:
        print('[Skipping] qBittorrent not running, skipping...')
        exit()
    if r_get.json():
        for torrent in r_get.json():
            if torrent['max_seeding_time'] == max_seeding_time and not 'paused' in torrent['state']:
                print('[Working] Pausing torrent "' + torrent['name'] + '"...')
                r_pause = requests.get('http://localhost:8080/api/v2/torrents/pause?hashes=' + torrent['hash'], \
                          cookies=r_auth.cookies.get_dict(), timeout=27.05)
                if r_pause.status_code == 200:
                    print('[Working] Torrent "' + torrent['name'] + '" paused.')
                    exit()
                else:
                    print('[Exception] Torrent "' + torrent['name'] + '" not paused.')
                    exit(1)
            else:
                continue
        print('[Skipping] No torrent eligible for clearing, skipping...')
        exit()
    else:
        print('[Skipping] No torrent, skipping...')
        exit()


if __name__ == "__main__":
    main()
