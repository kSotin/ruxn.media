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
from retrying import retry


def retry_if_requestexception(exception):
    return isinstance(exception, requests.exceptions.RequestException)


def send_statuses(sender_port, receiver_addr, receiver_port):
    data = json.dumps(statuses)
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.bind(('', sender_port))
    sender_socket.sendto(data.encode(), (receiver_addr, receiver_port))
    # print('[Syncing] Sent statuses to (' + str(receiver_addr) + ', ' + str(receiver_port) + ').')


def receive_statuses(receiver_port, index, sender_name):
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind(('', receiver_port))
    alivechecker = threading.Thread(target=receive_timeout_reset, args=(index, sender_name))
    alivechecker.start()
    while True:
        data, sender_addr = receiver_socket.recvfrom(2048)
        isalive[index] = True
        # print('[Syncing] Received statuses from ' + str(sender_addr) + '.')
        listofstatuses[index] = json.loads(data.decode())


def receive_timeout_reset(index, sender_name):
    clock = 0
    while True:
        if isalive[index]:
            isalive[index] = False
            clock = 0
        if clock == 250:
            print('[Checker Death] ' + sender_name.upper() + ' is dead.')
            listofstatuses[index] = None
            isalive[index] = False
            clock = 0
        time.sleep(1)
        clock += 1


def check_consistency(component):
    component_status = []
    for statuses in listofstatuses:
        if statuses != None:
            if component in statuses:
                component_status.append(statuses[component])
    if len(set(component_status)) == 1:
        return True
    else:
        return False


@retry(retry_on_exception=retry_if_requestexception)
def announce(status, component):
    while statuses[component] == status:
        if check_consistency(component):
            page_info = fetch_from_page()
            if statuses[component]:
                if page_info.get(components_id[component]) == 'major_outage':
                    print('[Announcing] Announcing restoration of ' + component.title() + '.')
                    r = requests.patch('https://api.statuspage.io/v1/pages/' + page_id + \
                        '/components/' + components_id[component], \
                        headers = {'Authorization': 'OAuth ' + API_key}, \
                        data = json.dumps({"component": {"status": "operational"}}), timeout=27.05)
                else:
                    print('[Skip-announcing] ' + component.title() + ' not to be updated, skipping...')
            else:
                if page_info.get(components_id[component]) == 'operational':
                    print('[Announcing] Announcing outage of ' + component.title() + '.')
                    r = requests.patch('https://api.statuspage.io/v1/pages/' + page_id + \
                        '/components/' + components_id[component], \
                        headers = {'Authorization': 'OAuth ' + API_key}, \
                        data = json.dumps({"component": {"status": "major_outage"}}), timeout=27.05)
                else:
                    print('[Skip-announcing] ' + component.title() + ' not to be updated, skipping...')
            break
        time.sleep(10)


def check_site(site_url):
    try:
        r = requests.get(site_url, timeout=27.05)
    except requests.exceptions.RequestException:
        return False
    else:
        if r.status_code == 200:
            return True
        else:
            return False


def check_proxy(proxy_url):
    s = requests.Session()
    s.mount('https://', host_header_ssl.HostHeaderSSLAdapter())
    try:
        r = s.get('https://' + proxy_url + '/statuscheck', headers={'Host': 'plex.ruxn.media'}, timeout=27.05)
    except requests.exceptions.RequestException:
        return False
    else:
        if r.status_code == 200:
            return True
        else:
            return False


def check_service(service):
    return_code = subprocess.call('systemctl is-active ' + service + '.service', \
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)
    if return_code == 0:
        return True
    else:
        return False


def check_timer(timer):
    timer_active = subprocess.call('systemctl is-active ' + timer + '.timer', \
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)
    service_failed = subprocess.call('systemctl is-failed ' + timer + '.service', \
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)
    if timer_active == 0 and service_failed != 0:
        return True
    else:
        return False


@retry(retry_on_exception=retry_if_requestexception)
def fetch_from_page():
    r = requests.get('https://api.statuspage.io/v1/pages/' + page_id + '/components', \
        headers = {'Authorization': 'OAuth ' + API_key}, timeout=27.05)
    statuses = {}
    for component_detail in r.json():
        statuses[component_detail['id']] = component_detail['status']
    return statuses


# main
try:
    opts, args = getopt.getopt(sys.argv[1:], "t:", ["tier="])
except getopt.GetoptError:
    print('Error: ' + sys.argv[0] + ' -t <tier>')
    print('       ' + sys.argv[0] + ' --tier=<tier>')
    sys.exit(2)
else:
    for opt, arg in opts:
        if opt in ("-t", "--tier"):
            tier = int(arg)

# Initialization
status_trans = {
    'operational': True,
    'major_outage': False,
}
listofstatuses = [statuses]
consistency = statuses.copy()
page_info = fetch_from_page()
for component in statuses:
    statuses[component] = status_trans.get(page_info.get(components_id[component]), True)

# Sync statuses - receiver
if tier != 0:
    listofthreads = []
    isalive = [True]
    indexofstatuses = 1
    for checker in sync_from_port:
        listofstatuses.append(None)
        listofthreads.append(threading.Thread(target=receive_statuses, \
            args=(sync_from_port[checker], indexofstatuses, checker)))
        listofthreads[-1].start()
        isalive.append(False)
        indexofstatuses += 1

while True:
    # Host
    if tier == 0:
        # Check services
        for service in services:
            if statuses[service]:
                if not check_service(service):
                    print('[Outage] An outage detected of ' + service + '.')
                    statuses[service] = False
                    announcer = threading.Thread(target=announce, args=(False, service))
                    announcer.start()
            else:
                if check_service(service):
                    print('[Restoration] Restoration from outage detected of ' + service + '.')
                    statuses[service] = True
                    announcer = threading.Thread(target=announce, args=(True, service))
                    announcer.start()
        # Check timers
        for timer in timers:
            if statuses[timer]:
                if not check_timer(timer):
                    print('[Outage] An outage detected of ' + timer + '.')
                    statuses[timer] = False
                    announcer = threading.Thread(target=announce, args=(False, timer))
                    announcer.start()
            else:
                if check_timer(timer):
                    print('[Restoration] Restoration from outage detected of ' + timer + '.')
                    statuses[timer] = True
                    announcer = threading.Thread(target=announce, args=(True, timer))
                    announcer.start()
    # Tier-1 proxy
    elif tier == 1:
        # Check sites
        for site in sites_url:
            if statuses[site]:
                if not check_site(sites_url[site]):
                    print('[Outage] An outage detected of ' + site.title() + '.')
                    statuses[site] = False
                    announcer = threading.Thread(target=announce, args=(False, site))
                    announcer.start()
            else:
                if check_site(sites_url[site]):
                    print('[Restoration] Restoration from outage detected of ' + site.title() + '.')
                    statuses[site] = True
                    announcer = threading.Thread(target=announce, args=(True, site))
                    announcer.start()
        # Check proxies
        for proxy in proxies_url:
            if statuses[proxy]:
                if not check_proxy(proxies_url[proxy]):
                    print('[Outage] An outage detected of ' + proxy.title() + '.')
                    statuses[proxy] = False
                    announcer = threading.Thread(target=announce, args=(False, proxy))
                    announcer.start()
            else:
                if check_proxy(proxies_url[proxy]):
                    print('[Restoration] Restoration from outage detected of ' + proxy.title() + '.')
                    statuses[proxy] = True
                    announcer = threading.Thread(target=announce, args=(True, proxy))
                    announcer.start()
    else:
        # Check proxies
        for proxy in proxies_url:
            if statuses[proxy]:
                if not check_proxy(proxies_url[proxy]):
                    print('[Outage] An outage detected of ' + proxy.title() + '.')
                    statuses[proxy] = False
                    announcer = threading.Thread(target=announce, args=(False, proxy))
                    announcer.start()
            else:
                if check_proxy(proxies_url[proxy]):
                    print('[Restoration] Restoration from outage detected of ' + proxy.title() + '.')
                    statuses[proxy] = True
                    announcer = threading.Thread(target=announce, args=(True, proxy))
                    announcer.start()
    # Sync statuses - sender
    if tier != 0:
        for checker in sync_receivers_port:
            send_statuses(sync_sender_port, checkers_addr[checker], sync_receivers_port[checker])

    time.sleep(15)
