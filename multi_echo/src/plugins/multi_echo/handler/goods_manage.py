from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from ..command import (
    set_goods,
    del_goods,
    set_onepack_goods,
    del_onepack_goods,
    set_min_price,
    set_rand_three_tail_three_pack_goods,
    del_rand_three_tail_three_pack_goods
)
from ..model.goods import Goods
from ..model.group_fee_rule import GroupFeeRule


# --------------------
# 工具函数
# --------------------
def _parse_goods_entries(entries: tuple[str, ...]) -> tuple[list[tuple[str, int]], list[str]]:
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
    return parsed, invalid


async def _get_current_min_price(session: async_scoped_session, bot_qq: str) -> int:
    result = await session.execute(
        select(Goods.min_price)
        .where(Goods.bot_qq == bot_qq)
        .limit(1)
    )
    current = result.scalar_one_or_none()
    return int(current) if current is not None else 0


async def _upsert_goods(
        session: async_scoped_session,
        bot_qq: str,
        model_cls,
        items: list[tuple[str, int]],
        goods_type: str,
        min_price: int
) -> None:
    for code, max_price in items:
        result = await session.execute(
            select(model_cls)
            .where(
                model_cls.bot_qq == bot_qq,
                model_cls.code == code,
                model_cls.goods_type == goods_type
            )
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            session.add(model_cls(
                bot_qq=bot_qq,
                code=code,
                max_price=max_price,
                min_price=min_price,
                goods_type=goods_type
            ))
        else:
            obj.max_price = max_price


async def _delete_goods(
        session: async_scoped_session,
        bot_qq: str,
        model_cls,
        entries: tuple[str, ...],
        goods_type: str
) -> int:
    deleted = 0
    for entry in entries:
        code = entry.split("-", 1)[0].strip()
        if not code:
            continue
        result = await session.execute(
            select(model_cls)
            .where(
                model_cls.bot_qq == bot_qq,
                model_cls.code == code,
                model_cls.goods_type == goods_type
            )
        )
        obj = result.scalar_one_or_none()
        if obj is not None:
            await session.delete(obj)
            deleted += 1
    return deleted


# --------------------
# 商品管理 Handler
# --------------------
@set_goods.handle()
async def handle_set_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    if not goods_list.available:
        return

    parsed, invalid = _parse_goods_entries(goods_list.result)
    if not parsed:
        await set_goods.finish("未解析到有效的代号-费用上限")
        return

    current_min_price = await _get_current_min_price(session, str(bot.self_id))
    await _upsert_goods(session, str(bot.self_id), Goods, parsed, "normal", current_min_price)
    await session.commit()

    if invalid:
        await set_goods.finish(f"已设置：{len(parsed)} 项，以下条目无效：{', '.join(invalid)}")
    else:
        await set_goods.finish(f"已设置：{len(parsed)} 项")


@del_goods.handle()
async def handle_del_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    if not goods_list.available:
        return

    deleted = await _delete_goods(session, str(bot.self_id), Goods, goods_list.result, "normal")
    await session.commit()
    await del_goods.finish(f"已删除：{deleted} 项")


@set_onepack_goods.handle()
async def handle_set_onepack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    if not goods_list.available:
        return

    parsed, invalid = _parse_goods_entries(goods_list.result)
    if not parsed:
        await set_onepack_goods.finish("未解析到有效的代号-费用上限")
        return

    current_min_price = await _get_current_min_price(session, str(bot.self_id))
    await _upsert_goods(session, str(bot.self_id), Goods, parsed, "onepack", current_min_price)
    await session.commit()

    if invalid:
        await set_onepack_goods.finish(f"已设置：{len(parsed)} 项，以下条目无效：{', '.join(invalid)}")
    else:
        await set_onepack_goods.finish(f"已设置：{len(parsed)} 项")


@del_onepack_goods.handle()
async def handle_del_onepack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_list: Match[tuple[str, ...]]
):
    if not goods_list.available:
        return

    deleted = await _delete_goods(session, str(bot.self_id), Goods, goods_list.result, "onepack")
    await session.commit()
    await del_onepack_goods.finish(f"已删除：{deleted} 项")


@set_rand_three_tail_three_pack_goods.handle()
async def handle_set_rand_three_tail_three_pack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_range: Match[tuple[str, ...]]
):
    if not goods_range.available:
        return
    parsed, invalid = _parse_goods_entries(goods_range.result)
    if not parsed:
        await set_rand_three_tail_three_pack_goods.finish("未解析到有效的代号-费用上限")
        return
    current_min_price = await _get_current_min_price(session, str(bot.self_id))
    await _upsert_goods(session, str(bot.self_id), Goods, parsed, "rand_three_tail_three_pack", current_min_price)
    await session.commit()
    if invalid:
        await set_rand_three_tail_three_pack_goods.finish(f"已设置：{len(parsed)} 项，以下条目无效：{', '.join(invalid)}")
    else:
        await set_rand_three_tail_three_pack_goods.finish(f"已设置：{len(parsed)} 项")


@del_rand_three_tail_three_pack_goods.handle()
async def handle_del_rand_three_tail_three_pack_goods(
        bot: Bot,
        session: async_scoped_session,
        goods_range: Match[tuple[str, ...]]
):
    if not goods_range.available:
        return
    deleted = await _delete_goods(session, str(bot.self_id), Goods, goods_range.result, "rand_three_tail_three_pack")
    await session.commit()
    await del_rand_three_tail_three_pack_goods.finish(f"已删除：{deleted} 项")


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
            GroupFeeRule.bot_qq == str(bot.self_id),
            GroupFeeRule.group_id == group_id,
        ).limit(1)
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        session.add(
            GroupFeeRule(
                bot_qq=str(bot.self_id),
                group_id=group_id,
                min_price=price,
            )
        )
    else:
        rule.min_price = price

    await session.commit()
    await set_min_price.finish(f"已设置该群费用下限：{price}")
