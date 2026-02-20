import disnake
from disnake.ext import commands
from pathlib import Path

from app.utils.viewer import GTAVTileViewer, Point


class PingCommand(commands.Cog):
    """This will be for a ping command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Абсолютный путь к assets относительно корня проекта
        self.assets_dir = Path(__file__).parent.parent.parent / "assets"

    @commands.slash_command()
    async def a(self, inter: disnake.ApplicationCommandInteraction, x: float, y: float):
        viewer = GTAVTileViewer(str(self.assets_dir))
        world_point = Point(x, y)

        fragment = viewer.get_fragment(
            world_point=world_point,
            size_x=1700,
            size_y=600,
        )

        output_path = "frag.jpeg"
        fragment.save(output_path, quality=100)
        await inter.response.send_message(
            f"/a {x} {y}",
            file=disnake.File(output_path)
        )


def setup(bot: commands.Bot):
    bot.add_cog(PingCommand(bot))
