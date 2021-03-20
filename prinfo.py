import requests
import re
import psycopg2
from bs4 import BeautifulSoup as bs
from datetime import datetime
import pytz

def loadConfig(config_name, params=[]):
    import configparser
    configs = configparser.ConfigParser()
    configs.read('config.ini')
    output = {}

    for param in params:
        try:
            parameter = configs.get(config_name, param)
            output[param] = parameter
        except Exception:
            continue
    return output


db_config = loadConfig("database", ["dbname", "user", "password"])

URL_TEMPLATE = "http://reality.otstrel.ru/monitoring_1.php"
try:
    r = requests.get(URL_TEMPLATE)
    soup = bs(r.text, "html.parser")
    info_block = soup.find_all('table', class_='borderAround')
    filtered_block = info_block[0].find_all('tr', class_='borderAround')
    map_block = soup.find_all('td', width='40%')
    map_html = map_block[0].find_all('font', class_='smallFont')
    players_raw = filtered_block[4].get_text()
    game_mode_raw = filtered_block[5].get_text()
    current_map_raw = map_html[2].get_text()
    # players_raw to normal
    temp = re.findall(r'\d+', players_raw)
    res = list(map(int, temp))
    players = res[0]

    # game_mode_raw to normal
    temp = re.compile('(\s*)gametype:(\s*)')
    game_mode = temp.sub('', game_mode_raw)[:-1]

    # current_map_raw to normal
    current_map = current_map_raw[2:]
except ConnectionRefusedError:
    print("No connection")
except Exception:
    print("Something went wrong")
else:
    print("Server available")
    mos_time = (datetime.now(pytz.timezone('Europe/Moscow')))

    # output to DB
    conn = psycopg2.connect(dbname=db_config['dbname'], user=db_config['user'],
                            password=db_config['password'], host='localhost')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO prosstat (map, g_mode, players, time) VALUES(%s, %s, %s, %s)",
                   (current_map, game_mode, players, mos_time))
    print("The entry was successfully added to DB")
    conn.commit()
    cursor.close()
    conn.close()


