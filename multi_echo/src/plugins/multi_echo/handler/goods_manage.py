from nonebot.adapters.onebot.v11 import Bot
from nonebot.matcher import Matcher
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from .cache import invalidate_goods_cache, invalidate_min_price_cache
from .echo import _normalize_code
from ..command import (
    del_goods,
    del_onepack_goods,
    del_rand_three_tail_three_pack_goods,
    set_goods,
    set_min_price,
    set_onepack_goods,
    set_rand_three_tail_three_pack_goods,
)
from ..model.goods import Goods
from ..model.group_fee_rule import GroupFeeRule


async def _handle_set_goods_by_type(
        matcher: type[Matcher],
        bot: Bot,
        session: async_scoped_session,
        entries: Match[tuple[str, ...]],
        goods_type: str,
) -> None:
    if not entries.available:
        return

    parsed, invalid, duplicated_count = _parse_goods_entries(entries.result)
    if not parsed:
        await matcher.finish("未解析到有效的代号-费用上限")
        return

    await _upsert_goods(session, bot.self_id, parsed, goods_type)
    await session.commit()
    for code, _ in parsed:
        invalidate_goods_cache(str(bot.self_id), goods_type, code)

    if invalid and duplicated_count:
        await matcher.finish(
            f"已设置：{len(parsed)} 项，移除重复项：{duplicated_count} 项，以下条目无效：{', '.join(invalid)}"
        )
    elif invalid:
        await matcher.finish(f"已设置：{len(parsed)} 项，以下条目无效：{', '.join(invalid)}")
    elif duplicated_count:
        await matcher.finish(f"已设置：{len(parsed)} 项，移除重复项：{duplicated_count} 项")
    else:
        await matcher.finish(f"已设置：{len(parsed)} 项")


async def _handle_del_goods_by_type(
        matcher: type[Matcher],
        bot: Bot,
        session: async_scoped_session,
        entries: Match[tuple[str, ...]],
        goods_type: str,
) -> None:
    if not entries.available:
        return

    deleted = await _delete_goods(session, bot.self_id, entries.result, goods_type)
    await session.commit()
    for entry in entries.result:
        norm = _normalize_code(entry.split("-", 1)[0])
        if norm:
            invalidate_goods_cache(str(bot.self_id), goods_type, norm)
    await matcher.finish(f"已删除：{deleted} 项")


@set_goods.handle()
async def handle_set_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    await _handle_set_goods_by_type(set_goods, bot, session, goods_list, "normal")


@del_goods.handle()
async def handle_del_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    await _handle_del_goods_by_type(del_goods, bot, session, goods_list, "normal")


@set_onepack_goods.handle()
async def handle_set_onepack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    await _handle_set_goods_by_type(set_onepack_goods, bot, session, goods_list, "onepack")


@del_onepack_goods.handle()
async def handle_del_onepack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    await _handle_del_goods_by_type(del_onepack_goods, bot, session, goods_list, "onepack")


@set_rand_three_tail_three_pack_goods.handle()
async def handle_set_rand_three_tail_three_pack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_range: Match[tuple[str, ...]]
):
    await _handle_set_goods_by_type(
        set_rand_three_tail_three_pack_goods, bot, session, goods_range, "rand_three_tail_three_pack"
    )


@del_rand_three_tail_three_pack_goods.handle()
async def handle_del_rand_three_tail_three_pack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_range: Match[tuple[str, ...]]
):
    await _handle_del_goods_by_type(
        del_rand_three_tail_three_pack_goods, bot, session, goods_range, "rand_three_tail_three_pack"
    )


@set_min_price.handle()
async def handle_set_min_price(
        bot: Bot,
        session: async_scoped_session,
        group: Match[int],
        min_price: Match[int]
):
    group_id = str(group.result)
    price = min_price.result
    result = await session.execute(
        select(GroupFeeRule).where(
            GroupFeeRule.bot_qq == bot.self_id,
            GroupFeeRule.group_id == group_id,
        ).limit(1)
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        session.add(
            GroupFeeRule(
                bot_qq=bot.self_id,
                group_id=group_id,
                min_price=price,
            )
        )
    else:
        rule.min_price = price

    await session.commit()
    invalidate_min_price_cache(str(bot.self_id), group_id)
    await set_min_price.finish(f"已设置该群费用下限：{price}")


def _parse_goods_entries(entries: tuple[str, ...]) -> tuple[list[tuple[str, int]], list[str], int]:
    parsed: list[tuple[str, int]] = []
    invalid: list[str] = []
    for entry in entries:
        if "-" not in entry:
            invalid.append(entry)
            continue
        code, limit = entry.split("-", 1)
        code = code.strip()
        limit = limit.strip()
        if not code or not limit.isdigit():
            invalid.append(entry)
            continue
        parsed.append((code, int(limit)))

    normalized: list[tuple[str, int]] = []
    seen_codes: set[str] = set()
    duplicated_count = 0
    for code, max_price in parsed:
        normalize_code = _normalize_code(code)
        if normalize_code in seen_codes:
            duplicated_count += 1
            continue
        seen_codes.add(normalize_code)
        normalized.append((normalize_code, max_price))

    return normalized, invalid, duplicated_count


async def _get_current_min_price(session: async_scoped_session, bot_qq: str) -> int:
    result = await session.execute(
        select(Goods.min_price)
        .where(Goods.bot_qq == bot_qq)
        .limit(1)
    )
    current = result.scalar_one_or_none()
    return current if current is not None else 0


async def _upsert_goods(
        session: async_scoped_session,
        bot_qq: str,
        items: list[tuple[str, int]],
        goods_type: str
) -> None:
    min_price = await _get_current_min_price(session, bot_qq)
    for code, max_price in items:
        result = await session.execute(
            select(Goods).where(
                Goods.bot_qq == bot_qq,
                Goods.code == code,
                Goods.goods_type == goods_type
            )
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            session.add(
                Goods(
                    bot_qq=bot_qq,
                    code=code,
                    max_price=max_price,
                    min_price=min_price,
                    goods_type=goods_type
                )
            )
        else:
            obj.max_price = max_price


async def _delete_goods(
        session: async_scoped_session,
        bot_qq: str,
        entries: tuple[str, ...],
        goods_type: str
) -> int:
    deleted = 0
    for entry in entries:
        code = _normalize_code(entry.split("-", 1)[0])
        if not code:
            continue
        result = await session.execute(
            select(Goods).where(
                Goods.bot_qq == bot_qq,
                Goods.code == code,
                Goods.goods_type == goods_type
            )
        )
        obj = result.scalar_one_or_none()
        if obj is not None:
            await session.delete(obj)
            deleted += 1
    return deleted
