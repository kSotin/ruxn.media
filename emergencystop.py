import requests
from credentials import *


def main():
    r_auth = requests.post('http://localhost:8080/api/v2/auth/login', \
             headers={'Referer': 'http://localhost:8080'}, \
             data={'username': qbtusername, 'password': qbtpassword})
    r_get = requests.get('http://localhost:8080/api/v2/torrents/info?filter=downloading', \
            cookies=r_auth.cookies.get_dict())
    if r_get.json():
        torrent_hashes = []
        for torrent in r_get.json():
            torrent_hashes.append(torrent['hash'])
        torrents_hash = torrent_hashes[0]
        for torrent_hash in torrent_hashes[1:]:
            torrents_hash += '|' + torrent_hash
        print('[Working] Pausing all downloading torrents...')
        r_pause = requests.get('http://localhost:8080/api/v2/torrents/pause?hashes=' + torrents_hash, \
                  cookies=r_auth.cookies.get_dict())
        i = 0
        while i < 2:
            if r_pause.status_code == 200:
                print('[Working] Paused ' + str(len(torrent_hashes)) + ' torrents.')
                exit()
            else:
                print('[Exception] Torrents not paused.')
                i += 1
        exit(1)
    else:
        print('[Skipping] No currently downloading torrents.')


if __name__ == "__main__":
    main()
