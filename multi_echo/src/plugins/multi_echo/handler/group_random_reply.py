from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..command import set_group_random_reply, switch_group_random_reply
from ..model.group_random_reply import GroupRandomReply


@set_group_random_reply.handle()
async def handle_set_group_random_reply(
        bot: Bot,
        session: async_scoped_session,
        group_id: Match[str],
        random_reduce_limit: Match[int]
):
    if not group_id.available or not random_reduce_limit.available:
        await set_group_random_reply.finish("参数错误，请输入正确的QQ群号和数字")
        return
    try:
        result = await session.execute(
            select(GroupRandomReply)
            .where(
                GroupRandomReply.bot_qq == bot.self_id,
                GroupRandomReply.group_id == group_id.result
            )
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            session.add(GroupRandomReply(
                bot_qq=bot.self_id,
                group_id=group_id.result,
                random_reduce_limit=random_reduce_limit.result
            ))
        else:
            obj.random_reduce_limit = random_reduce_limit.result
        await session.commit()
        await set_group_random_reply.finish(f"已设置群 {group_id.result} 随机减值上限为：{random_reduce_limit.result}")
    except SQLAlchemyError:
        await session.rollback()
        await set_group_random_reply.finish("数据库错误，设置失败")


@switch_group_random_reply.handle()
async def handle_switch_group_random_reply(
        bot: Bot,
        session: async_scoped_session,
        group_id: Match[str]
):
    if not group_id.available:
        await switch_group_random_reply.finish("参数错误，请输入正确的QQ群号")
        return
    try:
        result = await session.execute(
            select(GroupRandomReply)
            .where(
                GroupRandomReply.bot_qq == bot.self_id,
                GroupRandomReply.group_id == group_id.result
            )
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            session.add(GroupRandomReply(
                bot_qq=bot.self_id,
                group_id=group_id.result,
                enabled=True
            ))
            await session.commit()
            await switch_group_random_reply.finish(f"群 {group_id.result} 随机回复已开启")
        else:
            obj.enabled = not obj.enabled
            status = "开启" if obj.enabled else "关闭"  # 提前获取
            await session.commit()
            await switch_group_random_reply.finish(f"群 {group_id.result} 随机回复已{status}")
    except SQLAlchemyError:
        await session.rollback()
        await switch_group_random_reply.finish("数据库错误，操作失败")
