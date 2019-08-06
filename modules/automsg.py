from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import channel, message
from modules.util import bot, config, write_message
import re

scheduler = AsyncIOScheduler()

def setup(bot):
    for server in config:
        if bool(re.search(r'\d', server)) and config[server]['automsg']['enabled']:
            for message in config[server]['automsg']['messages']:
                for raw_time in message['time']:
                    scheduler.add_job(write_message, 'cron', day_of_week=raw_time['day'],
                                      hour=raw_time['hour'], minute=raw_time['minute'], second=raw_time['second'],
                                      args=[int(message['channel']), message['message']])
    scheduler.start()


def teardown(bot):
    scheduler.remove_all_jobs()