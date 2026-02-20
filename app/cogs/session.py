import disnake
from disnake.ext import commands
from dishka.integrations.disnake import DishkaAutoInjectMiddleware, FromDishka

from app.services.session_service import SessionService
from app.models.discord import SessionState


class SessionCog(commands.Cog):
    """Ког для управления сессиями."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(name="session_create", description="Создать новую сессию")
    async def session_create(
        self,
        inter: disnake.CommandInteraction,
        title: str = commands.Param(description="Заголовок сессии", max_length=100),
        description: str = commands.Param(
            description="Описание сессии",
            max_length=1000,
            default="",
        ),
        duration_hours: int = commands.Param(
            description="Длительность сессии в часах",
            default=24,
            min_value=1,
            max_value=168,
        ),
        color: str = commands.Param(
            description="Цвет сессии в HEX формате (например, #FF5733)",
            default=None,
        ),
        session_service: FromDishka[SessionService] = None,
    ):
        """Создать новую сессию."""
        await inter.response.defer()

        try:
            # Парсим цвет если указан
            parsed_color = None
            if color:
                from pydantic_extra_types.color import Color
                parsed_color = Color(color)

            session = await session_service.create_session(
                title=title,
                description=description or f"Сессия: {title}",
                color=parsed_color,
                duration_hours=duration_hours,
            )

            embed = disnake.Embed(
                title="✅ Сессия создана",
                description=f"**{session.title}**\n{session.description}",
                color=session.color.as_rgb_tuple(),
            )
            embed.add_field(name="ID", value=str(session.id), inline=False)
            embed.add_field(
                name="Создана",
                value=session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=True,
            )
            embed.add_field(
                name="Завершится",
                value=session.ends_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=True,
            )

            await inter.edit_original_response(embed=embed)

        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при создании сессии: {str(e)}"
            )

    @commands.slash_command(name="session_get", description="Получить информацию о сессии")
    async def session_get(
        self,
        inter: disnake.CommandInteraction,
        session_id: str = commands.Param(description="ID сессии"),
        session_service: FromDishka[SessionService] = None,
    ):
        """Получить информацию о сессии по ID."""
        await inter.response.defer()

        try:
            from uuid import UUID
            session_uuid = UUID(session_id)
            session = await session_service.get_session(session_uuid)

            if not session:
                await inter.edit_original_response(
                    content="❌ Сессия не найдена"
                )
                return

            embed = disnake.Embed(
                title="📋 Информация о сессии",
                description=f"**{session.title}**\n{session.description}",
                color=session.color.as_rgb_tuple(),
            )
            embed.add_field(name="ID", value=str(session.id), inline=False)
            embed.add_field(
                name="Создана",
                value=session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=True,
            )
            embed.add_field(
                name="Завершится",
                value=session.ends_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=True,
            )
            embed.add_field(
                name="Состояние",
                value=str(session.state.name),
                inline=True,
            )

            is_active = await session_service.is_session_active(session.id)
            embed.add_field(
                name="Активна",
                value="✅ Да" if is_active else "❌ Нет",
                inline=True,
            )

            await inter.edit_original_response(embed=embed)

        except ValueError:
            await inter.edit_original_response(
                content="❌ Неверный формат ID сессии"
            )
        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при получении сессии: {str(e)}"
            )

    @commands.slash_command(name="session_list", description="Показать все сессии")
    async def session_list(
        self,
        inter: disnake.CommandInteraction,
        session_service: FromDishka[SessionService] = None,
    ):
        """Показать список всех сессий."""
        await inter.response.defer()

        try:
            sessions = await session_service.get_all_sessions()

            if not sessions:
                await inter.edit_original_response(
                    content="📭 Нет активных сессий"
                )
                return

            embed = disnake.Embed(
                title="📋 Все сессии",
                description=f"Всего сессий: {len(sessions)}",
                color=disnake.Color.blue(),
            )

            for session in sessions[:10]:  # Показываем максимум 10
                is_active = await session_service.is_session_active(session.id)
                status = "🟢" if is_active else "🔴"
                embed.add_field(
                    name=f"{status} {session.title}",
                    value=f"ID: `{session.id}`\nДо: {session.ends_at.strftime('%H:%M %d.%m')}",
                    inline=False,
                )

            if len(sessions) > 10:
                embed.set_footer(text=f"... и ещё {len(sessions) - 10} сессий")

            await inter.edit_original_response(embed=embed)

        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при получении списка сессий: {str(e)}"
            )

    @commands.slash_command(name="session_update", description="Обновить сессию")
    async def session_update(
        self,
        inter: disnake.CommandInteraction,
        session_id: str = commands.Param(description="ID сессии"),
        title: str = commands.Param(description="Новый заголовок", default=None),
        description: str = commands.Param(description="Новое описание", default=None),
        color: str = commands.Param(description="Новый цвет в HEX", default=None),
        session_service: FromDishka[SessionService] = None,
    ):
        """Обновить параметры сессии."""
        await inter.response.defer()

        try:
            from uuid import UUID
            from pydantic_extra_types.color import Color

            session_uuid = UUID(session_id)

            parsed_color = Color(color) if color else None

            session = await session_service.update_session(
                session_id=session_uuid,
                title=title,
                description=description,
                color=parsed_color,
            )

            embed = disnake.Embed(
                title="✅ Сессия обновлена",
                description=f"**{session.title}**\n{session.description}",
                color=session.color.as_rgb_tuple(),
            )
            embed.add_field(name="ID", value=str(session.id), inline=False)

            await inter.edit_original_response(embed=embed)

        except ValueError as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка: {str(e)}"
            )
        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при обновлении сессии: {str(e)}"
            )

    @commands.slash_command(name="session_delete", description="Удалить сессию")
    async def session_delete(
        self,
        inter: disnake.CommandInteraction,
        session_id: str = commands.Param(description="ID сессии"),
        session_service: FromDishka[SessionService] = None,
    ):
        """Удалить сессию по ID."""
        await inter.response.defer()

        try:
            from uuid import UUID
            session_uuid = UUID(session_id)

            deleted = await session_service.delete_session(session_uuid)

            if deleted:
                await inter.edit_original_response(
                    content=f"✅ Сессия `{session_id}` удалена"
                )
            else:
                await inter.edit_original_response(
                    content="❌ Сессия не найдена"
                )

        except ValueError:
            await inter.edit_original_response(
                content="❌ Неверный формат ID сессии"
            )
        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при удалении сессии: {str(e)}"
            )

    @commands.slash_command(
        name="session_delete_all",
        description="⚠️ Удалить ВСЕ сессии"
    )
    async def session_delete_all(
        self,
        inter: disnake.CommandInteraction,
        confirm: bool = commands.Param(description="Подтвердить удаление", default=False),
        session_service: FromDishka[SessionService] = None,
    ):
        """Удалить все сессии. Требует подтверждения!"""
        if not confirm:
            await inter.response.send_message(
                "⚠️ Используйте `confirm=True` для подтверждения удаления всех сессий",
                ephemeral=True,
            )
            return

        await inter.response.defer()

        try:
            count = await session_service.delete_all_sessions()
            await inter.edit_original_response(
                content=f"✅ Удалено сессий: {count}"
            )

        except Exception as e:
            await inter.edit_original_response(
                content=f"❌ Ошибка при удалении сессий: {str(e)}"
            )


def setup(bot: commands.InteractionBot):
    """Добавить cog в бота."""
    bot.add_cog(SessionCog(bot))
