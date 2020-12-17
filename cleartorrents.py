import requests
from credentials import *


def main():
    r_auth = requests.post('http://localhost:8080/api/v2/auth/login', \
             headers={'Referer': 'http://localhost:8080'}, \
             data={'username': qbtusername, 'password': qbtpassword})
    r_get = requests.get('http://localhost:8080/api/v2/torrents/info?filter=completed&sort=completion_on', \
            cookies=r_auth.cookies.get_dict())
    if r_get.json():
        for torrent in r_get.json():
            if torrent['max_seeding_time'] == max_seeding_time and not 'paused' in torrent['state']:
                print('[Working] Pausing torrent "' + torrent['name'] + '"...')
                r_pause = requests.get('http://localhost:8080/api/v2/torrents/pause?hashes=' + torrent['hash'], \
                          cookies=r_auth.cookies.get_dict())
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
