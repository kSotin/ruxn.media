from credentials import *
import requests
import time
import json

def fetch_from_page():
    r = requests.get('https://api.statuspage.io/v1/pages/' + page_id + '/components', \
        headers = {'Authorization': 'OAuth ' + API_key})
    statuses = {}
    names = {}
    for component_detail in r.json():
        statuses[component_detail['id']] = component_detail['status']
        names[component_detail['id']] = component_detail['name']
    return statuses, names

def IFTTT_announce_outage(component_id):
    r = requests.post('https://maker.ifttt.com/trigger/ruxnmedia_outage/with/key/' + IFTTT_key, \
        data = {"value1": components_name[component_id]})

def IFTTT_announce_restoration(component_id):
    r = requests.post('https://maker.ifttt.com/trigger/ruxnmedia_restoration/with/key/' + IFTTT_key, \
        data = {"value1": components_name[component_id]})

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
        '/dns_records/' + cloudflare_recordid , headers=headers, data=data)

# main
# Initialization
status_trans = {
    'operational': True,
    'major_outage': False,
}
diff = statuses_full.copy()
page_info = fetch_from_page()
init_statuses = page_info[0]
components_name = page_info[1]
for component in statuses_full:
    statuses_full[component] = status_trans[init_statuses[components_id[component]]]
    diff[component] = False
new_statuses = statuses_full.copy()

while True:
    statuses = new_statuses.copy()
    new_page_info = fetch_from_page()
    for component in statuses_full:
        new_statuses[component] = status_trans[new_page_info[0][components_id[component]]]
        diff[component] = new_statuses[component] ^ statuses[component]

    # propagate
    # publish to IFTTT
    for component in statuses_full:
        if diff[component] == True:
            if new_statuses[component] == False:
                IFTTT_announce_outage(components_id[component])
                print("[IFTTT] Outage announced of " + component.title() + ".")
            else:
                IFTTT_announce_restoration(components_id[component])
                print("[IFTTT] Restoration announced of " + component.title() + ".")

    # switch to backup in-wall proxy
    if diff[main_inwall_proxy] == True:
        if new_statuses[main_inwall_proxy] == False:
            switch_inwall_proxy(True)
            print("[Proxy Switch] Switched to backup proxy.")
        else:
            switch_inwall_proxy(False)
            print("[Proxy Switch] Switched to main proxy.")

    time.sleep(10)
