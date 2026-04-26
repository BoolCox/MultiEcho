from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .utils import _valid_qq
from ..command import add_group, del_group
from ..model.group import Group


@add_group.handle()
async def handler_add_group(bot: Bot, session: async_scoped_session, qq: Match[str]):
    try:
        group = _valid_qq(str(qq.result))
    except ValueError:
        await add_group.finish("群号不合法")
        return

    try:
        result = await session.execute(
            select(Group).where(
                Group.bot_qq == bot.self_id,
                Group.platform_id == group,
            )
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            session.add(Group(bot_qq=bot.self_id, platform_id=group, enabled=True))
        else:
            obj.enabled = True
        await session.commit()
        await add_group.finish(f"已添加群：{group}")

    except IntegrityError:
        await session.rollback()
        await add_group.finish(f"已添加群：{group}")


@del_group.handle()
async def handler_del_group(bot: Bot, session: async_scoped_session, qq: Match[str]):
    try:
        group = _valid_qq(str(qq.result))
    except ValueError:
        await del_group.finish("群号不合法")
        return

    try:
        result = await session.execute(
            select(Group)
            .where(
                Group.bot_qq == bot.self_id,
                Group.platform_id == group
            )
        )
        obj = result.scalar_one_or_none()

        if obj is not None:
            obj.enabled = False
            await session.commit()

        await del_group.finish("已取消设置该群")

    except SQLAlchemyError:
        await session.rollback()
        await del_group.finish("数据库错误，取消失败")
