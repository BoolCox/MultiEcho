from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .utils import _valid_qq
from ..command import add_blocked_user, del_blocked_user
from ..model.blocked_user import BlockedUser


@add_blocked_user.handle()
async def handler_add_blocked_user(
        bot: Bot,
        session: async_scoped_session,
        qq: Match[str],
):
    try:
        user = _valid_qq(str(qq.result))
    except ValueError:
        await add_blocked_user.finish("QQ号不合法")
        return

    try:
        session.add(BlockedUser(bot_qq=bot.self_id, user_qq=user))
        await session.commit()
        await add_blocked_user.finish(f"已屏蔽用户：{user}")
    except IntegrityError:
        await session.rollback()
        await add_blocked_user.finish(f"已屏蔽用户：{user}")
    except SQLAlchemyError:
        await session.rollback()
        await add_blocked_user.finish("数据库错误，屏蔽失败")


@del_blocked_user.handle()
async def handler_del_blocked_user(
        bot: Bot,
        session: async_scoped_session,
        qq: Match[str],
):
    try:
        user = _valid_qq(str(qq.result))
    except ValueError:
        await del_blocked_user.finish("QQ号不合法")
        return

    try:
        result = await session.execute(
            select(BlockedUser).where(
                BlockedUser.bot_qq == bot.self_id,
                BlockedUser.user_qq == user,
            )
        )
        obj = result.scalar_one_or_none()

        if obj is not None:
            await session.delete(obj)
            await session.commit()

        await del_blocked_user.finish("已取消屏蔽该用户")
    except SQLAlchemyError:
        await session.rollback()
        await del_blocked_user.finish("数据库错误，取消失败")
