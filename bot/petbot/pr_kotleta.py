import discord
import psycopg2
from psycopg2 import sql
from discord.ext import commands, tasks
import os, sys
import pytz
import pickle
import re


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


bot_config = load_config("bot", ["TOKEN", "GUILD", "CHANNEL", "CHECK_DELAY", "BOT_CHANNEL"])
db_config = load_config("database", ["dbname", "table_name", "user", "password", "host"])
TOKEN = bot_config['TOKEN']
GUILD = os.getenv(bot_config['GUILD'])
bot = commands.Bot(command_prefix='!')
client = discord.Client()

bot.remove_command('help')


async def get_stats(manualy=False):
    await auto_refresh()

    conn = psycopg2.connect(dbname=db_config['dbname'], user=db_config['user'],
                            password=db_config['password'], host=db_config['host'])
    cursor = conn.cursor()
    cursor.execute(
        sql.SQL("SELECT map, g_mode, players, time FROM {} ORDER BY id DESC LIMIT 1")
        .format(sql.Identifier(db_config['table_name'])))
    print("Mapstats successfully readen from DB")
    rows = cursor.fetchall()
    for row in rows:
        map_name = str(row[0]).strip()
        game_mode = str(row[1]).strip()
        players_online = str(row[2]).strip()
        time = str(row[3].astimezone(pytz.timezone('Europe/Moscow'))).strip()[:19]
    cursor.close()
    conn.close()
    if int(players_online) > 20 or manualy:
        send_message = ('------------------------\n'
                        f'Time: {time}. \n'                        
                        f'Map: {map_name}. \n'
                        f'Game mode: {game_mode}. \n'
                        f'Players online: {players_online} \n'
                        '------------------------')
        await bot.get_channel(int(bot_config['CHANNEL'])).send(send_message)


async def auto_refresh():
    os.system('python ../stats/prinfo.py')


async def is_online(nickname: str):
    os.system(f'python ../stats/pstats.py online {nickname}')
    with open('../temp/data_to_bot', 'rb') as data_from_sctipt:
        response = pickle.load(data_from_sctipt)
    message_to_sent = "I've got next result:\n"
    if isinstance(response, list):
        for player in response:
            message_to_sent = message_to_sent + f"""Player: {player['Player']} \nOn server: {player['Server']} \n"""
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
            await message.delete()
            return

        elif not message.content.split()[0][1:] in bot.all_commands:
            await message.delete()
            return

        try:
            await bot.process_commands(message)
        except:
            await message.delete()


@tasks.loop(minutes=int(bot_config['CHECK_DELAY']))
async def stats_refresh():
    bot.loop.create_task(get_stats())


@bot.command(pass_context=True)
async def stats(ctx):
    await ctx.message.delete()
    await get_stats(manualy=True)


@bot.command(pass_context=True)
async def o(ctx, message=""):
    await ctx.message.delete()
    await ctx.message.author.send(await is_online(message))


@bot.command(pass_context=True)
async def s(ctx, message=""):
    await ctx.message.delete()
    pid = re.findall(r"[\d]+", message)
    if not pid:
        await ctx.message.author.send("You should give me ID")
    else:
        await ctx.message.author.send(await p_stats(int(pid[0])))

bot.run(TOKEN)
