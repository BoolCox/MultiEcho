import asyncio
import random
import re

from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..command import echo
from ..dependencies.profiler import AsyncProfiler
from ..exceptions import ReplyFeeExc
from ..model.blocked_user import BlockedUser
from ..model.delay import Delay
from ..model.goods import Goods, GoodsType
from ..model.group import Group
from ..model.group_fee_rule import GroupFeeRule
from ..model.group_random_reply import GroupRandomReply
from ..model.total_switch import TotalSwitch


@echo.handle()
async def handler_echo(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    profiler = AsyncProfiler()

    try:
        profiler.mark("start")

        parsed = _parse_and_validate_echo_command(event)
        profiler.mark("_parse")

        # 优化2：获取群实例且验证是否可用，一次查表
        group = await _ensure_echo_available(bot, event, session)
        profiler.mark("_ensure_echo_available")

        # 检查是否为被屏蔽用户
        await _ensure_not_blocked_user(bot, event, session)
        profiler.mark("_ensure_not_blocked_user")

        reply_fee = await _calculate_reply_fee(
            bot=bot,
            event=event,
            session=session,
            parsed=parsed
        )
        profiler.mark("_calculate_reply_fee")

        # 应用延迟
        await _apply_delay(bot, event, session)
        profiler.mark("_apply_delay")

        # 设置前缀
        prefix = _build_random_prefix(group)
        profiler.mark("_build_random_prefix")

    except (SQLAlchemyError, ReplyFeeExc):
        await session.rollback()
        return

    await echo.send(
        MessageSegment.at(event.get_user_id())
        + f"{prefix}{reply_fee}"
    )
    profiler.mark("send")
    profiler.report()


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
            Goods.code == normalized_code,
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_effective_min_price(bot: Bot, group_id: str, session: async_scoped_session) -> int:
    result = await session.execute(
        select(GroupFeeRule.min_price)
        .where(
            GroupFeeRule.bot_qq == bot.self_id,
            GroupFeeRule.group_id == group_id,
        )
        .limit(1)
    )
    group_min_price = result.scalar_one_or_none()
    if group_min_price is not None:
        return group_min_price
    else:
        return 0


async def get_group_random_reply_limit(bot: Bot, group_id: str, session: async_scoped_session) -> int:
    result = await session.execute(
        select(GroupRandomReply)
        .where(
            GroupRandomReply.bot_qq == bot.self_id,
            GroupRandomReply.group_id == group_id
        )
    )
    obj = result.scalar_one_or_none()
    return obj.random_reduce_limit if obj and obj.enabled and obj.random_reduce_limit else 0


async def _ensure_echo_available(
        bot: Bot,
        event: GroupMessageEvent,
        session: async_scoped_session
) -> Group:
    """确保插件/群组对该 bot 的 echo 功能可用；不可用时抛出 ReplyFeeExc；返回 Group 对象实例"""
    total_switch = await session.get(TotalSwitch, 1)
    if total_switch is None or not total_switch.enabled:
        raise ReplyFeeExc("功能未启用")

    result = await session.execute(
        select(Group).where(
            Group.bot_qq == bot.self_id,
            Group.platform_id == str(event.group_id),
            Group.enabled.is_(True),
        )
    )

    group = result.scalar_one_or_none()
    if not group:
        raise ReplyFeeExc("群未启用")

    return group


async def _ensure_not_blocked_user(
        bot: Bot,
        event: GroupMessageEvent,
        session: async_scoped_session
):
    """若用户被屏蔽则抛出 ReplyFeeExc，否则什么也不做"""
    result = await session.execute(
        select(BlockedUser).where(
            BlockedUser.bot_qq == bot.self_id,
            BlockedUser.user_qq == event.get_user_id(),
        )
    )

    if result.scalar_one_or_none() is not None:
        raise ReplyFeeExc("用户被屏蔽")


async def _apply_delay(
        bot: Bot,
        event: GroupMessageEvent,
        session: async_scoped_session
):
    result = await session.execute(
        select(Delay).where(
            Delay.group_id == str(event.group_id),
            Delay.bot_qq == bot.self_id
        )
    )

    delay_obj = result.scalar_one_or_none()

    delay_ms = delay_obj.delay if delay_obj else 0

    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000)


def _parse_and_validate_echo_command(event: GroupMessageEvent) -> tuple[str, int, GoodsType]:
    text = event.get_message().extract_plain_text().strip()

    patterns = [
        (re.fullmatch(r"收\s*2\s*/([^/]+)/(?P<fee>\d+)", text), GoodsType.NORMAL),
        (re.fullmatch(r"收2\s*/([^/]+)/(?P<fee>\d+)一包杀", text), GoodsType.ONEPACK),
        (re.fullmatch(r"拼随机三尾三包\s*([^/]+)/(?P<fee>\d+)", text), GoodsType.RAND_THREE_TAIL_THREE_PACK),
    ]

    for match, goods_type in patterns:
        if match:
            return (
                match.group(1).strip(),
                int(match.group("fee")),
                goods_type
            )

    # 不符合命令格式，通过抛出 ReplyFeeExc 让上层统一处理（handler_echo 捕获）
    raise ReplyFeeExc("命令格式不匹配")


async def _calculate_reply_fee(
        bot: Bot,
        event: GroupMessageEvent,
        session: async_scoped_session,
        parsed: tuple[str, int, GoodsType],
) -> int:
    code, fee, goods_type = parsed
    normalized_code = _normalize_code(code)
    if not normalized_code:
        # 无效 code
        raise ReplyFeeExc("无效的商品编码")

    goods = await _find_goods_by_code(
        event,
        session,
        goods_type,
        normalized_code
    )

    if goods is None:
        # 未找到对应商品
        raise ReplyFeeExc("未找到商品")

    effective_min_price = await _get_effective_min_price(
        bot,
        str(event.group_id),
        session
    )

    if fee < effective_min_price:
        # 低于群最低价
        raise ReplyFeeExc("出价低于最低价")

    reply_fee = min(fee, goods.max_price)

    random_reduce_limit = await get_group_random_reply_limit(
        bot,
        str(event.group_id),
        session
    )

    if random_reduce_limit > 0:
        minus = random.Random(str(event.time)).randint(
            0,
            random_reduce_limit
        )
        reply_fee = max(effective_min_price, reply_fee - minus)

    return reply_fee


def _build_random_prefix(group: Group) -> str:
    if not group.random_prefix_enabled:
        return ""

    symbols = [
        "·", "•", "☆", "★", "✦", "⚡", "♪", "♡", "❤", "※",
        "✪", "➤", "—", "~", "▪", "▫", "✿", "❀", "☘", "✧"
    ]

    return random.choice(symbols)
