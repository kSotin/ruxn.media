from credentials import *
import requests
import time
import json
import sys
import getopt
import subprocess


def fetch_from_page():
    r = requests.get('https://api.statuspage.io/v1/pages/' + page_id + '/components', \
        headers = {'Authorization': 'OAuth ' + API_key}, timeout=27.05)
    statuses = {}
    names = {}
    for component_detail in r.json():
        statuses[component_detail['id']] = component_detail['status']
        names[component_detail['id']] = component_detail['name']
    return statuses, names


def IFTTT_announce(component_name, new_status):
    r = requests.post('https://maker.ifttt.com/trigger/ruxnmedia_status_update/with/key/' + IFTTT_key, \
        data = {"value1": component_name, "value2": new_status.replace('_', ' ').capitalize()}, \
        timeout=27.05)


def switch_inwall_proxy(to_backup):
    headers = {
        'X-Auth-Email': cloudflare_email,
        'X-Auth-Key': cloudflare_key,
        'Content-Type': 'application/json',
    }
    if to_backup:
        data = '{"content":"' + inwall_backup_ip + '"}'
    else:
        data = '{"content":"' + inwall_main_ip + '"}'
    r = requests.patch('https://api.cloudflare.com/client/v4/zones/' + cloudflare_zoneid + \
        '/dns_records/' + cloudflare_recordid , headers=headers, data=data, timeout=27.05)


def switch_nginx_config(to_config):
    link_dir = '/etc/nginx/sites-enabled'
    primary_config = '/etc/nginx/sites-available/plex'
    secondary_config = '/etc/nginx/sites-available/plex_2'
    tertiary_config = '/etc/nginx/sites-available/plex_3'
    if to_config == 1:
        new_config = primary_config
    elif to_config == 2:
        new_config = secondary_config
    elif to_config == 3:
        new_config = tertiary_config

    remove_old_link = subprocess.run('rm ' + link_dir + '/plex*', shell=True)
    if remove_old_link.returncode == 0:
        create_new_link = subprocess.run('ln -s ' + new_config + ' ' + link_dir, shell=True)
        if create_new_link.returncode == 0:
            reload_nginx = subprocess.run('/usr/sbin/nginx -s reload', shell=True)
            if reload_nginx.returncode != 0:
                return False
        else:
            return False
    else:
        return False

    return True


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

    # Initialization
    diff = statuses_full.copy()
    page_info = fetch_from_page()
    components_name = page_info[1]
    for component in statuses_full:
        statuses_full[component] = page_info[0].get(components_id[component], 'operational')
        diff[component] = False
    new_statuses = statuses_full.copy()

    while True:
        statuses = new_statuses.copy()
        new_page_info = fetch_from_page()
        for component in statuses_full:
            new_statuses[component] = new_page_info[0].get(components_id[component], 'operational')
            diff[component] = new_statuses[component] != statuses[component]

        # propagators
        # Host
        if tier == 0:
            # publish to IFTTT
            for component in statuses_full:
                if diff[component] == True:
                    IFTTT_announce(components_name[components_id[component]], new_statuses[component])
                    print("[IFTTT] Status update announced of " + component.title() + ": " + \
                          new_statuses[component] + ".")

            # switch to backup in-wall proxy
            if diff[main_inwall_proxy] == True:
                if new_statuses[main_inwall_proxy] != 'operational':
                    switch_inwall_proxy(True)
                    print("[Proxy Switch] Switched to backup proxy.")
                else:
                    switch_inwall_proxy(False)
                    print("[Proxy Switch] Switched to main proxy.")
        # Tier-2 proxy
        elif tier == 2:
            if diff[tier1_1] == True:
                if new_statuses[tier1_1] != 'operational':
                    if new_statuses[tier1_2] == 'operational':
                        if switch_nginx_config(2) == True:
                            print("[Config Switch] Switched to secondary config.")
                        else:
                            print("[Config Switch] Config not switched.")
                    else:
                        if switch_nginx_config(3) == True:
                            print("[Config Switch] Switched to tertiary config.")
                        else:
                            print("[Config Switch] Config not switched.")
                else:
                    if switch_nginx_config(1) == True:
                        print("[Config Switch] Switched to primary config.")
                    else:
                        print("[Config Switch] Config not switched.")

        time.sleep(10)


if __name__ == "__main__":
   main(sys.argv)
