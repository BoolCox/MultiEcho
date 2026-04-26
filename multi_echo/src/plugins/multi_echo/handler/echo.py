import asyncio
import random
import re

from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..command import echo
from ..model.blocked_user import BlockedUser
from ..model.delay import Delay
from ..model.goods import Goods, GoodsType
from ..model.group import Group
from ..model.group_fee_rule import GroupFeeRule
from ..model.group_random_reply import GroupRandomReply
from ..model.total_switch import TotalSwitch


async def is_group_registered(bot: Bot, event: GroupMessageEvent, session: async_scoped_session) -> bool:
    result = await session.execute(
        select(Group)
        .where(
            Group.bot_qq == bot.self_id,
            Group.platform_id == str(event.group_id),
            Group.enabled.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


def _normalize_code(raw: str) -> str:
    code = raw.strip()
    if not code:
        return ""
    return "".join(sorted(code))


async def _find_goods_by_code(event, session, goods_type, normalized_code) -> Goods | None:
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


async def _get_effective_min_price(bot: Bot, group_id: str, session: async_scoped_session) -> int:
    result = await session.execute(
        select(GroupFeeRule.min_price)
        .where(
            GroupFeeRule.bot_qq == str(bot.self_id),
            GroupFeeRule.group_id == group_id,
        )
        .limit(1)
    )
    group_min_price = result.scalar_one_or_none()
    if group_min_price is not None:
        return int(group_min_price)
    else:
        return 0


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


async def is_group_random_prefix_enabled(bot: Bot, group_id: str, session: async_scoped_session) -> bool:
    """检查群是否开启随机前缀功能"""
    result = await session.execute(
        select(Group)
        .where(
            Group.bot_qq == str(bot.self_id),
            Group.platform_id == group_id,
        )
    )
    obj = result.scalar_one_or_none()
    return bool(obj and obj.random_prefix_enabled)


@echo.handle()
async def handler_echo(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    # 总开关和群启用状态校验
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
        effective_min_price = await _get_effective_min_price(bot, str(event.group_id), session)
        if fee < effective_min_price:
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
                reply_fee = max(effective_min_price, reply_fee - minus)

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
        # 如果群开启了随机前缀，从常见符号中随机挑一个并加在回复前面
        prefix = ""
        try:
            if await is_group_random_prefix_enabled(bot, str(event.group_id), session):
                symbols = [
                    "·", "•", "☆", "★", "✦", "⚡", "♪", "♡", "❤", "※",
                    "✪", "➤", "—", "~", "▪", "▫", "✿", "❀", "☘", "✧"
                ]
                prefix = random.choice(symbols)
        except SQLAlchemyError:
            # 如果检查前缀或随机选择出错，回退为无前缀，避免影响主逻辑
            prefix = ""

        await echo.send(MessageSegment.at(event.get_user_id()) + (prefix + str(reply_fee)))
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
