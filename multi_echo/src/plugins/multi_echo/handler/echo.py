import asyncio
import random
import re

from cachetools import TTLCache
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot_plugin_orm import get_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..command import echo
from ..exceptions import ReplyFeeExc
from ..model.blocked_user import BlockedUser
from ..model.delay import Delay
from ..model.goods import Goods, GoodsType
from ..model.group import Group
from ..model.group_fee_rule import GroupFeeRule
from ..model.group_random_reply import GroupRandomReply
from ..model.total_switch import TotalSwitch

total_switch_cache = TTLCache(maxsize=1, ttl=300)
group_cache = TTLCache(maxsize=1024, ttl=300)
block_cache = TTLCache(maxsize=1024, ttl=300)
min_price_cache = TTLCache(maxsize=1024, ttl=300)
random_reply_cache = TTLCache(maxsize=1024, ttl=300)
delay_cache = TTLCache(maxsize=1024, ttl=300)
goods_cache = TTLCache(maxsize=2048, ttl=300)


def invalidate_total_switch_cache() -> None:
    total_switch_cache.clear()


def invalidate_group_cache(bot_qq: str, group_id: str) -> None:
    group_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_block_cache(bot_qq: str, user_qq: str) -> None:
    block_cache.pop(f"{bot_qq}:{user_qq}", None)


def invalidate_min_price_cache(bot_qq: str, group_id: str) -> None:
    min_price_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_random_reply_cache(bot_qq: str, group_id: str) -> None:
    random_reply_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_delay_cache(bot_qq: str, group_id: str) -> None:
    delay_cache.pop(f"{bot_qq}:{group_id}", None)


def invalidate_goods_cache(bot_qq: str, goods_type: str, normalized_code: str) -> None:
    goods_cache.pop(f"{bot_qq}:{goods_type}:{normalized_code}", None)


def invalidate_all_goods_cache(bot_qq: str) -> None:
    prefix = f"{bot_qq}:"
    keys_to_delete = [k for k in goods_cache.keys() if k.startswith(prefix)]
    for k in keys_to_delete:
        goods_cache.pop(k, None)


_ECHO_PATTERNS = [
    (re.compile(r"收\s*2\s*/(?P<code>[^/]+)/(?P<fee>\d+)"), GoodsType.NORMAL),
    (re.compile(r"收\s*(?P<code>[^/]+)/(?P<fee>\d+)"), GoodsType.NORMAL),
    (re.compile(r"收2\s*/(?P<code>[^/]+)/(?P<fee>\d+)一包杀"), GoodsType.ONEPACK),
    (re.compile(r"收\s*(?P<code>[^/]+)/(?P<fee>\d+)一包杀"), GoodsType.ONEPACK),
    (re.compile(r"拼随机三尾三包\s*(?P<code>[^/]+)/(?P<fee>\d+)"), GoodsType.RAND_THREE_TAIL_THREE_PACK),
]


@echo.handle()
async def handler_echo(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    parsed = _parse_and_validate_echo_command(event)
    if parsed is None:
        return

    # 既然已匹配收车命令格式，无需再向后传播给 priority=5 的管理命令
    matcher.stop_propagation()

    try:
        # 获取群实例且验证是否可用
        group = await _ensure_echo_available(bot, event)

        # 检查是否为被屏蔽用户
        await _ensure_not_blocked_user(bot, event)

        reply_fee = await _calculate_reply_fee(
            bot=bot,
            event=event,
            parsed=parsed
        )

        # 应用延迟
        await _apply_delay(bot, event)

        # 设置前缀
        prefix = _build_random_prefix(group)

    except ReplyFeeExc as exc:
        logger.info(
            f"[echo] 未回复 group={event.group_id} bot={bot.self_id} "
            f"user={event.get_user_id()} reason={exc.message or exc}"
        )
        return
    except SQLAlchemyError:
        logger.exception(
            f"[echo] 数据库异常，未回复 group={event.group_id} bot={bot.self_id}"
        )
        return

    await echo.send(
        MessageSegment.at(event.get_user_id())
        + f"{reply_fee}{prefix}"
    )


def _normalize_code(raw: str) -> str:
    code = raw.strip()
    if not code:
        return ""
    return "".join(sorted(code))


async def _find_goods_by_code(event: GroupMessageEvent, goods_type: GoodsType, normalized_code: str) -> dict | None:
    bot_id = str(event.self_id)
    cache_key = f"{bot_id}:{goods_type.value}:{normalized_code}"
    if cache_key in goods_cache:
        return goods_cache[cache_key]

    async with get_session() as session:
        result = await session.execute(
            select(Goods.max_price)
            .where(
                Goods.bot_qq == bot_id,
                Goods.goods_type == goods_type.value,
                Goods.code == normalized_code,
            )
            .limit(1)
        )
        mp = result.scalar_one_or_none()

    res = {"max_price": mp} if mp is not None else None
    goods_cache[cache_key] = res
    return res


async def _get_effective_min_price(bot: Bot, group_id: str) -> int:
    cache_key = f"{bot.self_id}:{group_id}"
    if cache_key in min_price_cache:
        return min_price_cache[cache_key]

    async with get_session() as session:
        result = await session.execute(
            select(GroupFeeRule.min_price)
            .where(
                GroupFeeRule.bot_qq == bot.self_id,
                GroupFeeRule.group_id == group_id,
            )
            .limit(1)
        )
        group_min_price = result.scalar_one_or_none()

    effective_price = group_min_price if group_min_price is not None else 0
    min_price_cache[cache_key] = effective_price
    return effective_price


async def get_group_random_reply_limit(bot: Bot, group_id: str) -> int:
    cache_key = f"{bot.self_id}:{group_id}"
    if cache_key in random_reply_cache:
        return random_reply_cache[cache_key]

    async with get_session() as session:
        result = await session.execute(
            select(GroupRandomReply)
            .where(
                GroupRandomReply.bot_qq == bot.self_id,
                GroupRandomReply.group_id == group_id
            )
        )
        obj = result.scalar_one_or_none()

    val = obj.random_reduce_limit if obj and obj.enabled and obj.random_reduce_limit else 0
    random_reply_cache[cache_key] = val
    return val


async def _ensure_echo_available(
        bot: Bot,
        event: GroupMessageEvent,
) -> dict:
    """确保插件/群组对该 bot 的 echo 功能可用；不可用时抛出 ReplyFeeExc；返回包含群组状态字典"""
    if "enabled" in total_switch_cache:
        switch_enabled = total_switch_cache["enabled"]
    else:
        async with get_session() as session:
            total_switch = await session.get(TotalSwitch, 1)
            switch_enabled = bool(total_switch and total_switch.enabled)
        total_switch_cache["enabled"] = switch_enabled

    if not switch_enabled:
        raise ReplyFeeExc("功能未启用")

    cache_key = f"{bot.self_id}:{event.group_id}"
    if cache_key in group_cache:
        status = group_cache[cache_key]
    else:
        async with get_session() as session:
            result = await session.execute(
                select(Group).where(
                    Group.bot_qq == bot.self_id,
                    Group.platform_id == str(event.group_id),
                    Group.enabled.is_(True),
                )
            )
            group = result.scalar_one_or_none()

        status = {
            "has_group": bool(group),
            "random_prefix_enabled": group.random_prefix_enabled if group else False
        }
        group_cache[cache_key] = status

    if not status["has_group"]:
        raise ReplyFeeExc("群未启用")

    return status


async def _ensure_not_blocked_user(
        bot: Bot,
        event: GroupMessageEvent,
):
    """若用户被屏蔽则抛出 ReplyFeeExc，否则什么也不做"""
    cache_key = f"{bot.self_id}:{event.get_user_id()}"
    if cache_key in block_cache:
        is_blocked = block_cache[cache_key]
    else:
        async with get_session() as session:
            result = await session.execute(
                select(BlockedUser).where(
                    BlockedUser.bot_qq == bot.self_id,
                    BlockedUser.user_qq == event.get_user_id(),
                )
            )
            is_blocked = result.scalar_one_or_none() is not None
        block_cache[cache_key] = is_blocked

    if is_blocked:
        raise ReplyFeeExc("用户被屏蔽")


async def _apply_delay(
        bot: Bot,
        event: GroupMessageEvent,
):
    cache_key = f"{bot.self_id}:{event.group_id}"
    if cache_key in delay_cache:
        delay_ms = delay_cache[cache_key]
    else:
        async with get_session() as session:
            result = await session.execute(
                select(Delay).where(
                    Delay.group_id == str(event.group_id),
                    Delay.bot_qq == bot.self_id
                )
            )
            delay_obj = result.scalar_one_or_none()
        delay_ms = delay_obj.delay if delay_obj else 0
        delay_cache[cache_key] = delay_ms

    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000)


def _parse_and_validate_echo_command(event: GroupMessageEvent) -> tuple[str, int, GoodsType] | None:
    text = event.get_message().extract_plain_text().strip()
    if not text or not text.startswith(("收", "拼随机三尾三包")):
        return None

    for pattern, goods_type in _ECHO_PATTERNS:
        match = pattern.fullmatch(text)
        if match:
            return (
                match.group("code").strip(),
                int(match.group("fee")),
                goods_type,
            )

    return None


async def _calculate_reply_fee(
        bot: Bot,
        event: GroupMessageEvent,
        parsed: tuple[str, int, GoodsType],
) -> int:
    code, fee, goods_type = parsed
    normalized_code = _normalize_code(code)
    if not normalized_code:
        # 无效 code
        raise ReplyFeeExc("无效的商品编码")

    goods = await _find_goods_by_code(
        event,
        goods_type,
        normalized_code
    )

    if goods is None:
        # 未找到对应商品
        raise ReplyFeeExc("未找到商品")

    effective_min_price = await _get_effective_min_price(
        bot,
        str(event.group_id),
    )

    if fee < effective_min_price:
        # 低于群最低价
        raise ReplyFeeExc("出价低于最低价")

    reply_fee = min(fee, goods["max_price"])

    random_reduce_limit = await get_group_random_reply_limit(
        bot,
        str(event.group_id),
    )

    if random_reduce_limit > 0:
        minus = random.Random(str(event.time)).randint(
            0,
            random_reduce_limit
        )
        reply_fee = max(effective_min_price, reply_fee - minus)

    return reply_fee


def _build_random_prefix(group: dict) -> str:
    if not group.get("random_prefix_enabled"):
        return ""

    symbols = [
        "%", "(", "-", ".", ",", "#", "!", "*", "+"
    ]

    return random.choice(symbols)
