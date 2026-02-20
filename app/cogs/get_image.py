import disnake
from disnake.ext import commands


class GetImageCommand(commands.Cog):
    """This will be for a ping command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Multiplies the number by 7")
    async def multiply(self, inter, number: int):
        await inter.response.send_message(number * 7)

def setup(bot: commands.Bot):
    bot.add_cog(GetImageCommand(bot))