from discord.ext import commands
#TODO modules.util is bad, is there a better way?
import logging.handlers

# Initialize configuration
config = {}
# TODO aliases were never fully implemented in jerbot2, figure this out

logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.handlers.RotatingFileHandler(filename='jerbot-neo.log', encoding='utf-8', mode='w', maxBytes=1000000, backupCount=1)
logger.addHandler(handler)

bot = commands.Bot(command_prefix="!")
bot.config = config
#Util.load_modules(bot, config)

@bot.event
async def on_ready():
    print(f'Ready.\nLogged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # jerbot-neo can dynamically change bot prefixes per-server, we are hijacking on_message to change it
    # TODO change the config[] line to planned jerbot-neo method
    bot.command_prefix = config[str(message.guild.id)]['prefix']
    await bot.process_commands(message)
# TODO *global* error handling, none of this try/except trash every two lines
# TODO add help strings
# TODO proper permission management this time

print('Awaiting login.')

# TODO ability to define multiple tokens in config instead of having to hardcode testing's token
bot.run(config['main']['token'])