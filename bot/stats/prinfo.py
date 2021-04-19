import requests
import re
import psycopg2
from psycopg2 import sql
from bs4 import BeautifulSoup as bs
from datetime import datetime
import pytz


def loadConfig(config_name, params=[]):
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


db_config = loadConfig("database", ["dbname", "user", "password", "table_name"])

URL_TEMPLATE = "http://reality.otstrel.ru/monitoring_1.php"


def insert_to_db():
    cursor.execute(
        sql.SQL("INSERT INTO {} (map, g_mode, players, time) VALUES(%s, %s, %s, %s)")
        .format(sql.Identifier(db_config['table_name'])),
        (current_map, game_mode, players, mos_time))

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

    try:
        conn = psycopg2.connect(dbname=db_config['dbname'], user=db_config['user'],
                                password=db_config['password'])
        cursor = conn.cursor()
        cursor.execute('SAVEPOINT exception1')
        insert_to_db()
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
            insert_to_db
        else:
            print(f"Unknown exception. Resolve it fast as you can. Code is {e.pgcode}")
            cursor.execute('RELEASE SAVEPOINT exception1')
            exit(1)
    else:
        print(f"The entry was successfully added to DB at {str(mos_time)[:19]}")
        conn.commit()
        cursor.close()
        conn.close()
