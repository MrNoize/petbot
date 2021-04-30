import requests
import json
import pickle
import sys


STATS_URL = "https://servers.realitymod.com/api/ServerInfo"


def get_json(url):
    response = requests.get(url)
    if response.text == 'API calls quota exceeded! maximum admitted 2 per 60s.':
        with open('../temp/serverinfo.json', 'r', encoding='utf-8') as saved_json:
            raw_json = json.load(saved_json)
    else:
        raw_json = json.loads(response.text)
        with open('../temp/serverinfo.json', 'w', encoding='utf-8') as saved_json:
            json.dump(raw_json, saved_json)
    return raw_json


def is_player_online(nickname: str):
    returned_data = []
    try:
        with open('../configs/server_names.json', 'r', encoding='utf-8') as servers_id:
            servers_id_list = json.load(servers_id)
    except FileNotFoundError:
        print("Can't load server_names.json. Is it exist?")
        return "Unavailable"
    else:
        server_info = get_json(STATS_URL)
        for server in server_info['servers']:
            if server['serverId'] in servers_id_list:
                for player in server['players']:
                    if nickname.lower() in str(player['name']).strip().lower():
                        normalized_server = servers_id_list[server['serverId']]
                        returned_data.append({'Player': player['name'], 'Server': normalized_server})
    if not returned_data:
        return f"Player {nickname} is offline"
    else:
        return returned_data


with open('../temp/data_to_bot', 'wb') as data_to_bot:
    try:
        if len(str(sys.argv[1])) < 4:
            pickle.dump("Too short request. 4 symbols required", data_to_bot)
        else:
            pickle.dump(is_player_online(sys.argv[1]), data_to_bot)
    except IndexError:
        pickle.dump("You should give me a nickname", data_to_bot)