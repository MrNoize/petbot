import discord
from discord.ext import commands, tasks
from datetime import datetime
import os
import pytz
import pickle
import json
import re
import requests


STATS_URL = "https://servers.realitymod.com/api/ServerInfo"


def load_config(config_name, params=None):
    if params is None:
        params = []
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


def get_info():
    server_info = get_json(STATS_URL)
    players = 0
    game_mode = "PROS DOWN"
    current_map = "PROS DOWN"
    mos_time = str(datetime.now(pytz.timezone('Europe/Moscow')))[0:16]
    for server in server_info['servers']:
        if server['serverId'] == "8b946994d855bc356160a0ddf700bd29a72e7f60":
            players = server['properties']['numplayers']
            game_mode = server['properties']['gametype']
            current_map = server['properties']['mapname']
            print("Server available")
            return [players, game_mode, current_map, mos_time]
        else:
            continue
    print("PROS unavailable")
    return [players, game_mode, current_map, mos_time]


def read_maplist():
    with open("../temp/map_requests.json", "r", encoding="utf-8") as map_requests_json_read:
        return json.load(map_requests_json_read)


def add_to_mapreq_json(data):
    exist_data = read_maplist()
    with open("../temp/map_requests.json", "w", encoding="utf-8") as map_requests_json_write:
        read_dict = exist_data[1]['requests']
        for request in read_dict:
            if data['Nick'] == request['Nick']:
                read_dict.remove(request)
        read_dict.append(data)
        json.dump(exist_data, map_requests_json_write)


def delete_from_mapreq_json(data):
    exist_data = read_maplist()
    with open("../temp/map_requests.json", "w", encoding="utf-8") as map_requests_json_write:
        read_dict = exist_data[1]['requests']
        read_dict.remove(data)
        json.dump(exist_data, map_requests_json_write)


async def check_mapreq(current_map):
    requests_list = read_maplist()[1]['requests']
    for request in requests_list:
        if current_map.lower() == request['Map']:
            await bot.get_user(int(request['Player'])).send(f"You've requested map {request['Map']}.\n"
                                                            "It is on Russian reality right now.")
            delete_from_mapreq_json(request)


intents = discord.Intents.default()
intents.members = True

bot_config = load_config("bot", ["TOKEN", "GUILD", "CHANNEL", "CHECK_DELAY", "BOT_MODERATOR"])

TOKEN = bot_config['TOKEN']
bot = commands.Bot(command_prefix='!', intents=intents)
client = discord.Client(intents=intents)
maplist = read_maplist()[0]

bot.remove_command('help')


async def get_stats(manually=False):
    data = get_info()
    players_online = data[0]
    game_mode = data[1]
    map_name = data[2]
    time = data[3]
    if int(players_online) > 20 or manually:
        send_message = ('------------------------\n'
                        f'Time: {time}. \n'
                        f'Map: {map_name}. \n'
                        f'Game mode: {game_mode}. \n'
                        f'Players online: {players_online} \n'
                        '------------------------')
        print(send_message)
        await bot.get_channel(int(bot_config['CHANNEL'])).send(send_message)
    await check_mapreq(map_name)


async def auto_refresh():
    await get_stats(manually=False)


async def is_online(nickname: str):
    os.system(f'python ../stats/pstats.py online {nickname}')
    with open('../temp/data_to_bot', 'rb') as data_from_sctipt:
        response = pickle.load(data_from_sctipt)
    message_to_sent = "I've got next result:\n"
    if isinstance(response, list):
        for player in response:
            message_to_sent = message_to_sent + f"""\nPlayer: {player['Player']} \n
                                                      On server: {player['Server']} """
    elif isinstance(response, str):
        message_to_sent = response
    return message_to_sent


async def p_stats(pid: int):
    if isinstance(pid, int):
        os.system(f'python ../stats/pstats.py stats {pid}')
        with open('../temp/data_to_bot', 'rb') as data_from_sctipt:
            message_to_sent = pickle.load(data_from_sctipt)
        return message_to_sent
    else:
        return "ID should be an integer"


@bot.event
async def on_ready():
    stats_refresh.start()
    print('Kotleta ready to kill')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if str(message.channel.id) == str(bot_config['CHANNEL']):
        if not message.content.startswith("!"):
            if str(message.author) == str(bot_config['BOT_MODERATOR']):
                return
            else:
                await message.delete()
                return

        elif not message.content.split()[0][1:] in bot.all_commands:
            await message.delete()
            return

        try:
            await bot.process_commands(message)
            await message.delete()
        except:
            return


@tasks.loop(minutes=int(bot_config['CHECK_DELAY']))
async def stats_refresh():
    bot.loop.create_task(get_stats())


@bot.command(pass_context=True)
async def stats(ctx):
    await get_stats(manually=True)


@bot.command(pass_context=True)
async def o(ctx, message=""):
    await ctx.message.author.send(await is_online(message))


@bot.command(pass_context=True)
async def s(ctx, message=""):
    pid = re.findall(r"[\d]+", message)
    if not pid:
        await ctx.message.author.send("You should give me ID")
    else:
        await ctx.message.author.send(await p_stats(int(pid[0])))


@bot.command(pass_context=True)
async def req(ctx):
    mapname = ctx.message.content.strip('!req ')
    search_result = []
    for item in maplist:
        if mapname.lower() in item and not mapname == "" and len(mapname) > 3:
            search_result.append(item)
    if len(search_result) == 1:
        add_to_mapreq_json({"Player": ctx.message.author.id, "Nick": str(ctx.message.author.name), "Map": search_result[0], "Time": str(datetime.date(datetime.now(pytz.timezone('Europe/Moscow'))))})
        await ctx.message.author.send(f"I'll type you when {search_result[0]} will set on Russian Reality.")
    elif len(search_result) == 0:
        await ctx.message.author.send(f"Can't find any maps on request: {mapname}")
    else:
        await ctx.message.author.send(f"I found several maps on your request. Please, extend your request.\n"
                                      f" Maps on your request: {', '.join(search_result)}")


bot.run(TOKEN)
