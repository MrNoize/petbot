import discord
import psycopg2
from discord.ext import commands, tasks
import os
# FIRKA was here.


def loadConfig(config_name, params=[]):
    import configparser
    configs = configparser.ConfigParser()
    configs.read('../config.ini')
    output = {}

    for param in params:
        try:
            parameter = configs.get(config_name, param)
            output[param] = parameter
        except Exception:
            continue
    return output


bot_config = loadConfig("bot", ["TOKEN", "GUILD", "CHANNEL", "CHECK_DELAY", "BOT_CHANNEL"])
db_config = loadConfig("database", ["dbname", "user", "password"])
TOKEN = bot_config['TOKEN']
GUILD = os.getenv(bot_config['GUILD'])
bot = commands.Bot(command_prefix='!')
client = discord.Client()

bot.remove_command('help')


async def get_stats(manualy=False):
    await auto_refresh()
    conn = psycopg2.connect(dbname=db_config['dbname'], user=db_config['user'],
                            password=db_config['password'], host='localhost')
    cursor = conn.cursor()
    cursor.execute("SELECT map, g_mode, players, time FROM prosstat ORDER BY id DESC LIMIT 1")
    print("Mapstats successfully readen from DB")
    rows = cursor.fetchall()
    for row in rows:
        a = str(row[0]).strip()
        b = str(row[1]).strip()
        c = str(row[2]).strip()
        d = str(row[3]).strip()[:19]
    cursor.close()
    conn.close()
    if a and int(c) > 20 or manualy:
        send_message = ('------------------------\n'
                        f'Time: {d}. \n'                        
                        f'Map: {a}. \n'
                        f'Game mode: {b}. \n'
                        f'Players online: {c} \n'
                        '------------------------')
        await bot.get_channel(int(bot_config['CHANNEL'])).send(send_message)


async def auto_refresh():
    os.system('python ../stats/prinfo.py')


@bot.event
async def on_ready():
    stats_refresh.start()
    print('Kotleta ready to kill')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if str(message.channel) == str(bot_config['BOT_CHANNEL']):
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


bot.run(TOKEN)