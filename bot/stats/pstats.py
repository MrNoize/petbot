import json
import pickle
import sys
import requests
from bs4 import BeautifulSoup as Bs


STATS_URL = "https://servers.realitymod.com/api/ServerInfo"


def swap_values(list_to_swap: list):
    modified_list = []
    for item in list_to_swap:
        if (list_to_swap.index(item) % 2) == 0:
            modified_list.insert(list_to_swap.index(item)+1, item)
        else:
            modified_list.insert(list_to_swap.index(item)-1, item)
    return modified_list


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


def dump_to_temp(data):
    with open('../temp/data_to_bot', 'wb') as temp_file:
        pickle.dump(data, temp_file)


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


def parse_stats_by_id(pid: int):
    url_to_pstats = f"https://prstats.tk/player/{pid}/make_api"
    response = requests.get(url_to_pstats)
    if response.status_code == 200:
        soup = Bs(response.text, "html.parser")
        name_block = soup.find_all('div', class_='col-md-4 col-sm-12 col-xs-12 profile-text')
        info_block = soup.find_all('div', class_='col-md-2 col-sm-6 col-xs-6 profile-text mt mb centered')
        data_list = info_block[0].get_text().strip().split("\n")
        kd_list = info_block[1].get_text().strip().split("\n")
        name = name_block[0].get_text().split('\n')[1]
        return f" For player {name} with ID {pid}: \n {' '.join(swap_values(data_list))} \n {' '.join(swap_values(kd_list))}"
    elif response.status_code == 404:
        return f"Something went wrong[404]. \n Probably there is not any player with ID {pid}"
    else:
        return f"Can't give you any information. Site's status is {response.status_code}"


if sys.argv[1].strip() == "online":
    try:
        if len(str(sys.argv[2])) < 4:
            dump_to_temp("Too short request. 4 symbols required")
        else:
            dump_to_temp(is_player_online(sys.argv[2]))
    except IndexError:
        dump_to_temp("You should give me a nickname")

elif sys.argv[1].strip() == "stats":
    dump_to_temp(parse_stats_by_id(int(sys.argv[2])))
