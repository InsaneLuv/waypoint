import random
from pathlib import Path

import disnake
from dishka import FromDishka
from dishka_disnake.commands import slash_command
from dishka_disnake.ui import Button
from disnake.ext import commands

from app.models.discord import DiscordColor
from app.services import SessionService
from app.utils.viewer import GTAVTileViewer, Point


class But(Button):
    def __init__(self, text: str, session_uuid: str, style=disnake.ButtonStyle.gray, row: int | None = 0):
        self.session_uuid = session_uuid
        self.cur = [Point(x=2634.448, y=3292.035), Point(x=-1135.82, y=375.758)]
        self.iter = iter(self.cur)
        super().__init__(style=style, label=text, row=row)


class SwitchView(disnake.ui.View):
    def __init__(self, session_uuid: str):
        self.session_uuid = session_uuid
        super().__init__()

        self.add_item(StartSessionButton(text="🎲", session_uuid=session_uuid, style=disnake.ButtonStyle.blurple))


class StartSessionButton(But):
    async def callback(self, inter: disnake.MessageInteraction, session_service: FromDishka[SessionService]):
        await inter.response.defer()
        await inter.edit_original_response(
            embed=None,
            files=[],
        )
        viewer = GTAVTileViewer(str(Path(__file__).parent.parent.parent / "assets"))
        ps = next(self.iter)

        fragment = viewer.get_fragment(
            world_point=ps,
            size_x=800,
            size_y=600,
            dot_color="red"
        )

        output_path = "frag.jpeg"
        fragment.save(output_path, quality=100)
        msg = await inter.edit_original_response(
            embed=None,
            files=[disnake.File(output_path)],
            attachments=[],
            view=SwitchView(session_uuid=self.session_uuid)
        )


class JoinSessionButton(But):
    async def callback(self, inter: disnake.MessageInteraction, session_service: FromDishka[SessionService]):
        await inter.response.defer()
        await inter.edit_original_response(
            content=f"❌ не чёто не хочу пока",
            embed=None
        )


class DestroySessionButton(But):
    async def callback(self, inter: disnake.MessageInteraction, session_service: FromDishka[SessionService]):
        await inter.response.defer()
        await inter.edit_original_response(
            content=f"❌ не чёто не хочу пока",
            embed=None
        )


class SessionView(disnake.ui.View):

    def __init__(self, session_uuid: str):
        super().__init__()
        self.add_item(StartSessionButton(text="📍 Начать", session_uuid=session_uuid, style=disnake.ButtonStyle.green))
        self.add_item(
            JoinSessionButton(text="🔗 Присоединится", session_uuid=session_uuid, style=disnake.ButtonStyle.blurple))
        self.add_item(
            DestroySessionButton(text="🧨 Пиздец", session_uuid=session_uuid, style=disnake.ButtonStyle.secondary))

    def check_board_winner(self):
        return None


class SessionCog(commands.Cog):
    """Ког для управления сессиями."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    def _build_participants_list(self, participants: list, author_id: int | None = None) -> str:
        """Сформировать строку со списком участников."""
        if not participants:
            return "Нет участников"

        lines = []
        for p in participants:
            marker = "👑" if p.user_id == author_id else ""
            lines.append(f"- {p.username} {marker}")
        return "\n".join(lines)

    def _build_session_embed(self, session, participants_list: str) -> disnake.Embed:
        """Создать embed для сессии."""
        embed = disnake.Embed(
            title="*Waypoint* сессия",
            description=session.description,
            color=int(session.color.as_hex()[1:], 16) if session.color else DiscordColor.random().value,
        )
        embed.add_field(
            name="Участники",
            value=participants_list,
            inline=False,
        )
        embed.set_footer(text=f"{session.id}")
        return embed

    @slash_command(name="new", description="Создать новую сессию")
    async def new(
            self,
            inter: disnake.CommandInteraction,
            session_service: FromDishka[SessionService],
    ):
        """Создать новую сессию."""
        await inter.response.defer()
        title = f"{inter.user.display_name} сессия"
        duration_hours = 0
        try:
            session = await session_service.create_session(
                title=title,
                description="",
                author_id=inter.user.id,
                author_username=inter.user.display_name,
                duration_hours=duration_hours,
            )

            participants_list = self._build_participants_list(
                session.participants, session.author_id
            )
            embed = self._build_session_embed(session, participants_list)
            embed.set_author(
                name=inter.user.display_name,
                icon_url=inter.user.display_avatar.url,
            )
            await inter.edit_original_response(embed=embed, view=SessionView(session.id))

        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при создании сессии: {str(e)}"
            )


def setup(bot: commands.InteractionBot):
    bot.add_cog(SessionCog(bot))
