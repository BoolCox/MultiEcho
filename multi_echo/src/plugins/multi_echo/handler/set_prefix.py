from nonebot.adapters.onebot.v11 import Bot
from nonebot.matcher import Matcher
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .cache import invalidate_group_cache
from ..command import disable_random_prefix, open_random_prefix
from ..model.group import Group


async def _set_group_random_prefix(
        matcher: type[Matcher],
        bot: Bot,
        session: async_scoped_session,
        group_id: str,
        enabled: bool,
) -> None:
    try:
        group_obj: Group | None = await session.scalar(
            select(Group)
            .where(
                Group.platform_id == group_id,
                Group.bot_qq == str(bot.self_id),
            )
        )

        if group_obj:
            group_obj.random_prefix_enabled = enabled
        else:
            session.add(
                Group(
                    bot_qq=str(bot.self_id),
                    platform_id=group_id,
                    random_prefix_enabled=enabled
                )
            )

        await session.commit()
        invalidate_group_cache(str(bot.self_id), str(group_id))

        await matcher.finish("已开启群压车符号" if enabled else "已关闭群压车符号")
    except SQLAlchemyError:
        await session.rollback()
        await matcher.finish("数据库错误，设置失败")


@open_random_prefix.handle()
async def open_random_prefix_func(
        bot: Bot,
        session: async_scoped_session,
        group: Match[str]
):
    await _set_group_random_prefix(open_random_prefix, bot, session, group.result, True)


@disable_random_prefix.handle()
async def disable_random_prefix_func(
        bot: Bot,
        session: async_scoped_session,
        group: Match[str]
):
    await _set_group_random_prefix(disable_random_prefix, bot, session, group.result, False)
