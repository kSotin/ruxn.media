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
    for component in statuses_full:
        new_statuses[component] = status_trans[fetch_from_page()[0][components_id[component]]]
        diff[component] = new_statuses[component] ^ statuses[component]

    # propagate
    for component in statuses_full:
        if diff[component] == True:
            if new_statuses[component] == False:
                IFTTT_announce_outage(components_id[component])
            else:
                IFTTT_announce_restoration(components_id[component])

    time.sleep(10)
