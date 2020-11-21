from credentials import *
import time
import threading
import requests
import json
from requests_toolbelt.adapters import host_header_ssl
import socket
import sys
import getopt
import subprocess


# For status syncing
def send_statuses(statuses, sender_port, receiver_addr, receiver_port):
    data = json.dumps(statuses)
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.bind(('', sender_port))
    sender_socket.sendto(data.encode(), (receiver_addr, receiver_port))
    print('[Syncing] Sent statuses to (' + str(receiver_addr) + ', ' + str(receiver_port) + ').')


def receive_statuses(receiver_port, list, index, sender_name, isalive):
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind(('', receiver_port))
    alivechecker = threading.Thread(target=receive_timeout_reset, args=(list, index, sender_name, isalive))
    alivechecker.start()
    while True:
        data, sender_addr = receiver_socket.recvfrom(2048)
        isalive[index] = True
        print('[Syncing] Received statuses from ' + str(sender_addr) + '.')
        list[index] = json.loads(data.decode())


def receive_timeout_reset(list, index, sender_name, isalive):
    clock = 0
    while True:
        if isalive[index]:
            isalive[index] = False
            clock = 0
        if clock == 600:
            print('[Checker Death] ' + sender_name.upper() + ' is dead.')
            for component in list[index]:
                list[index][component] = True
            isalive[index] = False
            clock = 0
        time.sleep(1)
        clock += 1


def merge_statuses(merge_to, merge_from):
    for statuses in merge_from:
        for component in statuses:
            merge_to[component] = merge_to[component] and statuses[component]


# For status checking

def check_site(site_url, isDown):
    i = 0
    while i < 2:
        try:
            r = requests.get(site_url)
        except requests.exceptions.RequestException:
            if isDown:
                return False
            else:
                i += 1
        else:
            if r.status_code == 200:
                return True
            else:
                return False
    return False


def check_back_end(service):
    return_code = subprocess.call('systemctl is-active ' + service, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)
    if return_code == 0:
        return True
    else:
        return False


def check_proxy(proxy_url, isDown):
    s = requests.Session()
    s.mount('https://', host_header_ssl.HostHeaderSSLAdapter())
    i = 0
    while i < 2:
        try:
            r = s.get('https://' + proxy_url, headers={'Host': 'plex.ruxn.media'})
        except requests.exceptions.RequestException:
            if isDown:
                return False
            else:
                i += 1
        else:
            if r.status_code == 401 or r.status_code == 502:
                return True
            else:
                return False
    return False


def fetch_from_page():
    r = requests.get('https://api.statuspage.io/v1/pages/' + page_id + '/components', \
        headers = {'Authorization': 'OAuth ' + API_key})
    statuses = {}
    for component_detail in r.json():
        statuses[component_detail['id']] = component_detail['status']
    return statuses


def announce_outage(component_id):
    r = requests.patch('https://api.statuspage.io/v1/pages/' + page_id + '/components/' + component_id, \
        headers = {'Authorization': 'OAuth ' + API_key}, \
        data = json.dumps({"component": {"status": "major_outage"}}))


def announce_restoration(to_announce, listofstatuses):
    time.sleep(30)
    lock.acquire()
    try:
        merge_statuses(statuses, listofstatuses[1:])
        for component in list(to_announce):
            if statuses[component]:
                print('[Announcing] Announcing restoration of ' + component.title() + '.')
                r = requests.patch('https://api.statuspage.io/v1/pages/' + page_id + '/components/' + components_id[component], \
                    headers = {'Authorization': 'OAuth ' + API_key}, \
                    data = json.dumps({"component": {"status": "operational"}}))
                to_announce.remove(component)
    finally:
        lock.release()


lock = threading.Lock()


def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "t:", ["tier="])
    except getopt.GetoptError:
        print('Error: ' + argv[0] + ' -t <tier>')
        print('       ' + argv[0] + ' --tier=<tier>')
        sys.exit(2)
    else:
        for opt, arg in opts:
            if opt in ("-t", "--tier"):
                tier = int(arg)

    # Initialize statuses
    status_trans = {
        'operational': True,
        'major_outage': False,
    }
    init_statuses = fetch_from_page()
    for component in statuses:
        statuses[component] = status_trans[init_statuses[components_id[component]]]
    to_announce = set()
    listofstatuses = [statuses]

    # Sync statuses - receiver
    if tier != 0:
        listofthreads = []
        isalive = [True]
        indexofstatuses = 1
        for checker in sync_from_port:
            listofstatuses.append(statuses.copy())
            listofthreads.append(threading.Thread(target=receive_statuses, name=checker, args=(sync_from_port[checker], listofstatuses, indexofstatuses, checker, isalive)))
            listofthreads[-1].start()
            isalive.append(False)
            indexofstatuses += 1

    while True:
        # Host
        if tier == 0:
            # Check plex
            if not check_back_end('plexmediaserver') and statuses['plex media server']:
                print('[Outage] An outage detected of PMS.')
                announce_outage(components_id['plex media server'])
                statuses['plex media server'] = False
            if check_back_end('plexmediaserver') and not statuses['plex media server']:
                print('[Restoration] Restoration from outage detected of PMS.')
                statuses['plex media server'] = True
                to_announce.add('plex media server')
            # Check back-end services
            for service in services:
                if not check_back_end(service) and statuses[service]:
                    print('[Outage] An outage detected of ' + service + '.')
                    announce_outage(components_id[service])
                    statuses[service] = False
                if check_back_end(service) and not statuses[service]:
                    print('[Restoration] Restoration from outage detected of ' + service + '.')
                    statuses[service] = True
                    to_announce.add(service)
        # Tier-1 proxy
        elif tier == 1:
            # Check sites
            for site in sites_url:
                if statuses[site]:
                    if check_site(sites_url[site], False):
                        print('[Outage] An outage detected of ' + site.title() + '.')
                        announce_outage(components_id[site])
                        statuses[site] = False
                if !statuses[site]:
                    if check_site(sites_url[site], True):
                        print('[Restoration] Restoration from outage detected of ' + site.title() + '.')
                        statuses[site] = True
                        to_announce.add(site)
            # Check proxies
            for proxy in proxies_url:
                if statuses[proxy]:
                    if check_proxy(proxies_url[proxy], False):
                        print('[Outage] An outage detected of ' + proxy.title() + '.')
                        announce_outage(components_id[proxy])
                        statuses[proxy] = False
                if !statuses[proxy]:
                    if check_proxy(proxies_url[proxy], True):
                        print('[Restoration] Restoration from outage detected of ' + proxy.title() + '.')
                        statuses[proxy] = True
                        to_announce.add(proxy)
        else:
            # Check proxies
            for proxy in proxies_url:
                if statuses[proxy]:
                    if check_proxy(proxies_url[proxy], False):
                        print('[Outage] An outage detected of ' + proxy.title() + '.')
                        announce_outage(components_id[proxy])
                        statuses[proxy] = False
                if !statuses[proxy]:
                    if check_proxy(proxies_url[proxy], True):
                        print('[Restoration] Restoration from outage detected of ' + proxy.title() + '.')
                        statuses[proxy] = True
                        to_announce.add(proxy)
        # Reset own status
        if 'myself' in locals() or 'myself' in globals():
            statuses[myself] = True
        # Sync statuses - sender
        if tier != 0:
            for checker in sync_receivers_port:
                send_statuses(statuses, sync_sender_port, checkers_addr[checker], sync_receivers_port[checker])
                # time.sleep(5)
                # send_statuses(statuses, sync_sender_port, checkers_addr[checker], sync_receivers_port[checker])
        # Announce restoration
        announcer = threading.Thread(target=announce_restoration, args=(to_announce, listofstatuses))
        announcer.start()

        time.sleep(15)


if __name__ == "__main__":
   main(sys.argv)
