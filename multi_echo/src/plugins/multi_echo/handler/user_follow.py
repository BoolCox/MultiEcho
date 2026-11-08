from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .utils import _valid_qq
from ..model.follow import Follow
from ..command import follow_user, unfollow_user


@follow_user.handle()
async def handler_follow_user(
        event: GroupMessageEvent,
        session: async_scoped_session,
        qq: Match[str]
):
    try:
        bot_id = str(event.self_id)
        user_id = _valid_qq(str(qq.result))
    except ValueError:
        await follow_user.finish("QQ号不合法")
        return

    try:
        session.add(Follow(bot_id=bot_id, user_id=user_id))
        await session.commit()
    except IntegrityError:
        await session.rollback()

    await follow_user.finish(f"已跟随：{user_id}")


@unfollow_user.handle()
async def handler_unfollow_user(
        event: GroupMessageEvent,
        session: async_scoped_session,
        qq: Match[str]
):
    try:
        bot_id = str(event.self_id)
        user_id = _valid_qq(str(qq.result))
    except ValueError:
        await unfollow_user.finish("QQ号不合法")
        return

    try:
        result = await session.execute(
            select(Follow)
            .where(
                Follow.bot_id == bot_id,
                Follow.user_id == user_id
            )
        )
        obj = result.scalar_one_or_none()

        if obj is not None:
            await session.delete(obj)
            await session.commit()

        await unfollow_user.finish("已取消跟随")

    except SQLAlchemyError:
        await session.rollback()
        await unfollow_user.finish("数据库错误，取消失败")
