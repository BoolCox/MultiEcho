import asyncio
import random
import re

from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from ..command import echo
from ..model.blocked_user import BlockedUser
from ..model.delay import Delay
from ..model.goods import Goods, GoodsType
from ..model.group import Group
from ..model.group_random_reply import GroupRandomReply
from ..model.total_switch import TotalSwitch


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


async def _find_goods_by_code(event, session, goods_type, normalized_code):
    result = await session.execute(
        select(Goods)
        .where(
            Goods.bot_qq == str(event.self_id),
            Goods.goods_type == goods_type.value,
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


async def get_group_random_reply_count(bot: Bot, group_id: str, session: async_scoped_session) -> int:
    result = await session.execute(
        select(GroupRandomReply)
        .where(
            GroupRandomReply.bot_qq == str(bot.self_id),
            GroupRandomReply.group_id == group_id
        )
    )
    obj = result.scalar_one_or_none()
    return obj.count if obj and obj.enabled and obj.count else 0


@echo.handle()
async def handler_echo(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    # 总开关和白名单校验
    result = await session.get(TotalSwitch, 1)
    if result is None or not result.enabled or not await is_group_registered(bot, event, session):
        return

    # 检查群随机回复开关（不开启则正常回复）
    random_reply_enabled = await is_group_random_reply_enabled(bot, str(event.group_id), session)

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

    # 三种命令正则
    match_normal = re.fullmatch(r"收\s*2\s*/([^/]+)/(?P<fee>\d+)", message_text)
    match_onepack = re.fullmatch(r"收2\s*/([^/]+)/(?P<fee>\d+)一包杀", message_text)
    match_rand = re.fullmatch(r"拼随机三尾三包\s*([^/]+)/(?P<fee>\d+)", message_text)
    code, fee, goods_type = None, None, None
    if match_normal:
        code = match_normal.group(1).strip()
        fee = int(match_normal.group("fee"))
        goods_type = GoodsType.NORMAL
    elif match_onepack:
        code = match_onepack.group(1).strip()
        fee = int(match_onepack.group("fee"))
        goods_type = GoodsType.ONEPACK
    elif match_rand:
        code = match_rand.group(1).strip()
        fee = int(match_rand.group("fee"))
        goods_type = GoodsType.RAND_THREE_TAIL_THREE_PACK

    reply_fee = None

    if code and fee is not None and goods_type:
        normalized_code = _normalize_code(code)
        if not normalized_code:
            return
        goods = await _find_goods_by_code(event, session, goods_type, normalized_code)
        if goods is None:
            return
        if fee < goods.min_price:
            return
        if fee > goods.max_price:
            reply_fee = goods.max_price
        else:
            reply_fee = fee

        # 仅在开关开启时，随机减去范围内的数字
        if random_reply_enabled:
            random_reply_count = await get_group_random_reply_count(bot, str(event.group_id), session)
            if random_reply_count > 0:
                # 直接用 event.message_id 作为随机种子
                minus = random.Random(str(event.time)).randint(0, random_reply_count)
                reply_fee = max(goods.min_price, reply_fee - minus)

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


async def is_group_random_reply_enabled(bot: Bot, group_id: str, session: async_scoped_session) -> bool:
    result = await session.execute(
        select(GroupRandomReply)
        .where(
            GroupRandomReply.bot_qq == str(bot.self_id),
            GroupRandomReply.group_id == group_id
        )
    )
    obj = result.scalar_one_or_none()
    return bool(obj and obj.enabled)
