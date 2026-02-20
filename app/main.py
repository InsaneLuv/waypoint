from dishka import make_async_container
from dishka_disnake import setup_dishka
from disnake.ext import commands

from app.deps import (
    ConfigProvider, RedisProvider, SessionServiceProvider,
)
from app.core.config import get_app_settings

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True
bot = commands.InteractionBot(reload=True, command_sync_flags=command_sync_flags)


@bot.event
async def on_ready():
    """Prints a message when the bot successfully connects to Discord."""
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")


def run():
    settings = get_app_settings()
    container = make_async_container(
        ConfigProvider(),
        RedisProvider(),
        SessionServiceProvider(),
    )

    # Настраиваем интеграцию dishka с disnake
    setup_dishka(container=container)

    # Загружаем cog
    bot.load_extension("app.cogs.ping")
    bot.load_extension("app.cogs.animals")
    bot.load_extension("app.cogs.get_image")
    bot.load_extension("app.cogs.session")

    bot.run(settings.app.BOT_TOKEN.get_secret_value())


if __name__ == '__main__':
    run()
