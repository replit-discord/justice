from gevent.monkey import patch_all; patch_all()

import logging
from os import environ

from disco.bot import Bot, BotConfig
from disco.client import Client, ClientConfig
from disco.util.logging import setup_logging


setup_logging(level=logging.INFO)
config = ClientConfig.from_file("config.json")
config.token = environ['token']
client = Client(config)
bot_config = BotConfig(config.bot)
bot = Bot(client, bot_config)

if __name__ == '__main__':
    bot.run_forever()
