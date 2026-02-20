from disnake.ext import commands
from dishka import make_async_container
from dishka.integrations.disnake import setup_dishka

from app.deps import (
    ConfigProvider,
    RedisProvider,
    SessionServiceProvider,
)

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True
bot = commands.InteractionBot(reload=True, command_sync_flags=command_sync_flags)


@bot.event
async def on_ready():
    """Prints a message when the bot successfully connects to Discord."""
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")


bot_token = "123"

if bot_token:
    # Создаём DI контейнер
    container = make_async_container(
        ConfigProvider(),
        RedisProvider(),
        SessionServiceProvider(),
    )

    # Настраиваем интеграцию dishka с disnake
    setup_dishka(container=container, bot=bot)

    # Загружаем cog'и
    bot.load_extension("app.cogs.ping")
    bot.load_extension("app.cogs.animals")
    bot.load_extension("app.cogs.get_image")
    bot.load_extension("app.cogs.session")

    bot.run(bot_token)

else:
    print("Error: BOT_TOKEN environment variable not set. Please set it to your bot's token.")
