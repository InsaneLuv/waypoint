import disnake
from dishka import FromDishka
from dishka_disnake.commands import slash_command
from disnake.ext import commands

from app.models.discord import DiscordColor
from app.services import SessionService


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
            marker = "👑" if p.user_id == author_id else "•"
            lines.append(f"{marker} {p.username}")
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
        embed.set_footer(text=f"ID: {session.id}")
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
        description = f"Сессия создана пользователем {inter.user.display_name}"
        duration_hours = 0
        try:
            session = await session_service.create_session(
                title=title,
                description=description,
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
            await inter.edit_original_response(embed=embed)

        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при создании сессии: {str(e)}"
            )

    @slash_command(name="join", description="Войти в сессию")
    async def join(
            self,
            inter: disnake.CommandInteraction,
            session_id: str,
            session_service: FromDishka[SessionService],
    ):
        """Войти в сессию по ID."""
        await inter.response.defer()
        try:
            from uuid import UUID
            uuid = UUID(session_id)
        except ValueError:
            await inter.edit_original_response(
                content="❌ Неверный формат ID сессии"
            )
            return

        try:
            session = await session_service.join_session(
                session_id=uuid,
                user_id=inter.user.id,
                username=inter.user.display_name,
            )

            participants_list = self._build_participants_list(
                session.participants, session.author_id
            )
            embed = self._build_session_embed(session, participants_list)
            await inter.edit_original_response(embed=embed)

        except ValueError as e:
            await inter.edit_original_response(
                content=f"❌ Сессия не найдена: {str(e)}"
            )
        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при входе в сессию: {str(e)}"
            )

    @slash_command(name="leave", description="Выйти из сессии")
    async def l(
            self,
            inter: disnake.CommandInteraction,
            session_id: str,
            session_service: FromDishka[SessionService],
    ):
        """Выйти из сессии по ID."""
        await inter.response.defer()
        try:
            from uuid import UUID
            uuid = UUID(session_id)
        except ValueError:
            await inter.edit_original_response(
                content="❌ Неверный формат ID сессии"
            )
            return

        try:
            session = await session_service.leave_session(
                session_id=uuid,
                user_id=inter.user.id,
            )

            participants_list = self._build_participants_list(
                session.participants, session.author_id
            )
            embed = self._build_session_embed(session, participants_list)
            await inter.edit_original_response(embed=embed)

        except ValueError as e:
            await inter.edit_original_response(
                content=f"❌ Сессия не найдена: {str(e)}"
            )
        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при выходе из сессии: {str(e)}"
            )


def setup(bot: commands.InteractionBot):
    """Добавить cog в бота."""
    bot.add_cog(SessionCog(bot))
