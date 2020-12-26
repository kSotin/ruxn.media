import requests
import subprocess
import time
from credentials import *


threshold_low = 85
threshold_high = 95
drive = '/dev/sda3'


limited = False
stopped = False
torrent_hashes = []


def check_qbt():
    check_qbt = subprocess.run('systemctl is-active qbittorrent', \
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)
    if check_qbt.returncode == 0:
        return True
    else:
        return False


def toggle_stopped(to_stop):
    global stopped
    global torrent_hashes
    if check_qbt():
        r_auth = requests.post('http://localhost:8080/api/v2/auth/login', \
                 headers={'Referer': 'http://localhost:8080'}, \
                 data={'username': qbtusername, 'password': qbtpassword}, timeout=27.05)
        cookies = r_auth.cookies.get_dict()
        if to_stop:
            # Pause all downloads
            r_get = requests.get('http://localhost:8080/api/v2/torrents/info?filter=downloading', \
                    cookies=cookies, timeout=27.05)
            if r_get.json():
                torrent_hashes.clear()
                for torrent in r_get.json():
                    torrent_hashes.append(torrent['hash'])
                torrents_hash = torrent_hashes[0]
                for torrent_hash in torrent_hashes[1:]:
                    torrents_hash += '|' + torrent_hash
                r_pause = requests.get('http://localhost:8080/api/v2/torrents/pause?hashes=' + torrents_hash, \
                          cookies=cookies, timeout=27.05)
                if r_pause.status_code == 200:
                    print('[Working] Paused ' + str(len(torrent_hashes)) + ' torrents.')
                    stopped = True
                else:
                    print('[Exception] Torrents not paused.')
                    exit(1)
            else:
                print('[Skipping] No currently downloading torrents.')
        else:
            # Resume previously paused torrents
            torrents_hash = torrent_hashes[0]
            for torrent_hash in torrent_hashes[1:]:
                torrents_hash += '|' + torrent_hash
            r_resume = requests.get('http://localhost:8080/api/v2/torrents/resume?hashes=' + torrents_hash, \
                       cookies=cookies, timeout=27.05)
            if r_resume.status_code == 200:
                print('[Working] Resumed ' + str(len(torrent_hashes)) + ' torrents.')
                stopped = False
            else:
                print('[Exception] Torrents not resumed.')
                exit(1)
    else:
        print('[Skipping] qBittorrent not running.')


def toggle_limited(to_limit):
    global limited
    if check_qbt():
        r_auth = requests.post('http://localhost:8080/api/v2/auth/login', \
                 headers={'Referer': 'http://localhost:8080'}, \
                 data={'username': qbtusername, 'password': qbtpassword}, timeout=27.05)
        cookies = r_auth.cookies.get_dict()
        # Get alternative speed limit state
        r_alt_state = requests.get('http://localhost:8080/api/v2/transfer/speedLimitsMode', \
                      cookies = cookies, timeout=27.05)
        if to_limit:
            # Toggle alternative download speed
            if r_alt_state.text == '0':
                r_toggle_alt_state = requests.get('http://localhost:8080/api/v2/transfer/toggleSpeedLimitsMode', \
                                     cookies = cookies, timeout=27.05)
                if r_toggle_alt_state.status_code == 200:
                    limited = True
                    print('[Limit] Download speed limited.')
                else:
                    print('[Exception] Download speed not limited.')
                    exit(1)
            else:
                print('[Skipping] Download speed limit already applied.')
        else:
            # Toggle alternative download speed
            if r_alt_state.text == '1':
                r_toggle_alt_state = requests.get('http://localhost:8080/api/v2/transfer/toggleSpeedLimitsMode', \
                                     cookies = cookies, timeout=27.05)
                if r_toggle_alt_state.status_code == 200:
                    limited = False
                    print('[Undo-Limit] Download speed limit lifted.')
                else:
                    print('[Exception] Download speed limit not lifted.')
                    exit(1)
            else:
                print('[Skipping] Download speed limit already lifted.')
    else:
        print('[Skipping] qBittorrent not running.')


def main():
    while True:
        # Get disk usage
        check_usage = subprocess.run("df -h | grep " + drive + " | awk '{print $5}' | sed 's/%//'", \
                      shell=True, stdout=subprocess.PIPE)
        if check_usage.returncode != 0:
            exit(1)
        used = int(check_usage.stdout)
        print('[Notice] Disk usage: ' + str(used) + '%.')

        if used >= threshold_high:
            print('[Stop] Disk usage: ' + str(used) + '%, pausing all downloads')
            toggle_stopped(1)
        elif used < threshold_high and used >= threshold_low:
            if stopped:
                print('[Undo-Stop] Disk usage: ' + str(used) + '%, resuming previously paused torrents...')
                toggle_stopped(0)
            if not limited:
                print('[Limit] Disk usage: ' + str(used) + '%, limiting download speed...')
                toggle_limited(1)
        elif used < threshold_low:
            if stopped:
                print('[Undo-Stop] Disk usage: ' + str(used) + '%, resuming previously paused torrents...')
                toggle_stopped(0)
            if limited:
                print('[Undo-Limit] Disk usage: ' + str(used) + '%, lifting download speed limit...')
                toggle_limited(0)


        time.sleep(300)


if __name__ == "__main__":
    main()
