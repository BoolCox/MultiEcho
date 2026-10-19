from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..command import open_random_prefix, disable_random_prefix
from ..model.group import Group


@open_random_prefix.handle()
async def open_random_prefix_func(
        bot: Bot,
        session: async_scoped_session,
        group: Match[str]
):
    try:
        group_obj: Group | None = await session.scalar(
            select(Group)
            .where(
                Group.platform_id == group.result,
                Group.bot_qq == str(bot.self_id),
            )
        )

        if group_obj:
            group_obj.random_prefix_enabled = True
        else:
            session.add(
                Group(
                    bot_qq=str(bot.self_id),
                    platform_id=group.result,
                    random_prefix_enabled=True
                )
            )

        await session.commit()

        await open_random_prefix.finish("已开启群压车符号")
    except SQLAlchemyError:
        await session.rollback()
        await open_random_prefix.finish("数据库错误，设置失败")


@disable_random_prefix.handle()
async def disable_random_prefix_func(
        bot: Bot,
        session: async_scoped_session,
        group: Match[str]
):
    try:
        group_obj: Group | None = await session.scalar(
            select(Group)
            .where(
                Group.platform_id == group.result,
                Group.bot_qq == str(bot.self_id),
            )
        )

        if group_obj:
            group_obj.random_prefix_enabled = False
        else:
            session.add(
                Group(
                    bot_qq=str(bot.self_id),
                    platform_id=group.result,
                    random_prefix_enabled=False
                )
            )

        await session.commit()

        await disable_random_prefix.finish("已关闭群压车符号")
    except SQLAlchemyError:
        await session.rollback()
        await disable_random_prefix.finish("数据库错误，设置失败")
