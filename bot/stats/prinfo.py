import psycopg2
from psycopg2 import sql
from datetime import datetime
import pytz
import json
import requests

STATS_URL = "https://servers.realitymod.com/api/ServerInfo"


def load_config(config_name, params=[]):
    import configparser
    configs = configparser.ConfigParser()
    configs.read('../configs/config.ini')
    output = {}

    for param in params:
        try:
            parameter = configs.get(config_name, param)
            output[param] = parameter
        except Exception:
            continue
    return output


db_config = load_config("database", ["dbname", "user", "password", "table_name", "host"])

URL_TEMPLATE = "http://reality.otstrel.ru/monitoring_1.php"


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


def insert_to_db(cursor, current_map, game_mode, players, mos_time):
    cursor.execute(
        sql.SQL("INSERT INTO {} (map, g_mode, players, time) VALUES(%s, %s, %s, %s)")
        .format(sql.Identifier(db_config['table_name'])),
        (current_map, game_mode, players, mos_time))


def db_action(current_map, game_mode, players, mos_time):
    try:
        conn = psycopg2.connect(dbname=db_config['dbname'], user=db_config['user'],
                                password=db_config['password'], host=db_config['host'])
        cursor = conn.cursor()
        cursor.execute('SAVEPOINT exception1')
        insert_to_db(cursor, current_map, game_mode, players, mos_time)
    except psycopg2.ProgrammingError as e:
        cursor.execute('ROLLBACK TO SAVEPOINT exception1')
        if e.pgcode == "42P01":
            print('Table from configs not found. Creating new table with next params:')
            print(f"  Create table {db_config['table_name']}(id serial, map character(20) NOT NULL, "
                  f"g_mode character(20) NOT NULL, players integer NOT NULL, time timestamp with time zone NOT NULL)")
            cursor.execute(
                sql.SQL('''Create table {} 
                (id serial, map character(20) NOT NULL,
                g_mode character(20) NOT NULL,
                players integer NOT NULL,
                time timestamp with time zone NOT NULL);''')
                    .format(sql.Identifier(db_config['table_name']))
            )
            print(f"Successfully created {db_config['table_name']}")
            conn.commit()
            insert_to_db(cursor, current_map, game_mode, players, mos_time)
        else:
            print(f"Unknown exception. Resolve it fast as you can. Code is {e.pgcode}")
            cursor.execute('RELEASE SAVEPOINT exception1')
            cursor.close()
            conn.close()
            exit(1)
    else:
        print(f"The entry was successfully added to DB at {str(mos_time)[:19]}")
        conn.commit()
        cursor.close()
        conn.close()


server_info = get_json(STATS_URL)
def get_info():
    for server in server_info['servers']:
        if server['serverId'] == "8b946994d855bc356160a0ddf700bd29a72e7f60":
            players = server['properties']['numplayers']
            game_mode = server['properties']['gametype']
            current_map = server['properties']['mapname']
            print("Server available")
            mos_time = (datetime.now(pytz.timezone('Europe/Moscow')))
            db_action(current_map, game_mode, players, mos_time)
            return 1
        else:
            continue
    return 0


if get_info() == 0:
    print("PROS unavailable")
    db_action(current_map = "PROS_DOWN", game_mode = "-", players = "0", mos_time = (datetime.now(pytz.timezone('Europe/Moscow'))))
else:
    print("Everything is ok")
