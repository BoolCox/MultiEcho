import asyncio
import re

from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from ..command import echo
from ..model.delay import Delay
from ..model.goods import Goods
from ..model.group import Group
from ..model.total_switch import TotalSwitch
from ..model.blocked_user import BlockedUser


async def is_group_registered(bot: Bot, event: GroupMessageEvent, session: async_scoped_session) -> bool:
    result = await session.execute(
        select(Group)
        .where(
            Group.bot_qq == bot.self_id,
            Group.platform_id == event.group_id,
        )
    )
    return result.scalar_one_or_none() is not None


def _normalize_code(raw: str) -> str:
    code = raw.strip()
    if not code:
        return ""
    return "".join(sorted(code))


async def _find_goods_by_code(
        event: GroupMessageEvent,
        session: async_scoped_session,
        is_onepack: bool,
        normalized_code: str,
) -> Goods | None:
    result = await session.execute(
        select(Goods)
        .where(
            Goods.bot_qq == str(event.self_id),
            Goods.is_onepack == is_onepack,
        )
    )
    return next(
        (
            item
            for item in result.scalars().all()
            if _normalize_code(item.code) == normalized_code
        ),
        None,
    )


@echo.handle()
async def handler_echo(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    # 总开关和白名单校验
    result = await session.get(TotalSwitch, 1)
    if result is None or not result.enabled or not await is_group_registered(bot, event, session):
        return

    # 检查是否为被屏蔽用户
    blocked_res = await session.execute(
        select(BlockedUser).where(
            BlockedUser.bot_qq == bot.self_id,
            BlockedUser.user_qq == event.get_user_id(),
        )
    )
    if blocked_res.scalar_one_or_none() is not None:
        return

    message_text = event.get_message().extract_plain_text().strip()

    code: str | None = None
    fee: int | None = None
    is_onepack: bool = False

    match = re.fullmatch(r"收2\s*/([^/]+)/(?P<fee>\d+)(?P<onepack>一包杀)?", message_text)
    if match:
        code = match.group(1).strip()
        fee = int(match.group("fee"))
        is_onepack = match.group("onepack") is not None
    else:
        match_new = re.fullmatch(r"拼随机三尾三包\s*([^/]+)/(?P<fee>\d+)", message_text)
        if match_new:
            code = match_new.group(1).strip()
            fee = int(match_new.group("fee"))
            is_onepack = False

    reply_fee: int | None = None

    if code is not None and fee is not None:
        if not code:
            return
        # 这里不再校验商品编码的格式，允许非数字的代号

        # 校验费用
        normalized_code = _normalize_code(code)
        if not normalized_code:
            return
        goods = await _find_goods_by_code(event, session, is_onepack, normalized_code)
        if goods is None:
            return
        if fee < goods.min_price:
            return
        if fee > goods.max_price:
            reply_fee = goods.max_price
        else:
            reply_fee = fee

    # 从数据库读取延迟
    res = await session.execute(
        select(Delay)
        .where(
            Delay.group_id == str(event.group_id),
            Delay.bot_qq == bot.self_id
        )
    )
    delay_obj = res.scalar_one_or_none()
    delay_ms = delay_obj.delay if delay_obj else 0
    if delay_ms and delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000)

    if reply_fee is not None:
        await echo.send(MessageSegment.at(event.get_user_id()) + str(reply_fee))
        return
