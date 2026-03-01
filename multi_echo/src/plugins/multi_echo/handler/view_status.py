from nonebot import get_bots
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, delete

from ..command import view_status, view_whitelist_group, del_goods_all
from ..model.goods import Goods
from ..model.group import Group
from ..model.total_switch import TotalSwitch


@view_status.handle()
async def handler_view_status(event: GroupMessageEvent, session: async_scoped_session):
    num = len(get_bots())

    # 计算本群是否启用跟随（总开关开启 且 本群在白名单中）
    total_switch = await session.get(TotalSwitch, 1)
    total_enabled = bool(total_switch and total_switch.enabled)
    res = await session.execute(
        select(Group).where(
            Group.bot_qq == str(event.self_id),
            Group.platform_id == event.group_id
        )
    )
    in_whitelist = bool(res.scalar_one_or_none())
    group_status = "可用" if (total_enabled and in_whitelist) else "不可用"

    await view_status.finish(
        "当前状态\n"
        f"- 当前在线账号数：{num}\n"
        f"- 本群{group_status}\n"
    )


@view_whitelist_group.handle()
async def handler_view_whitelist_group(session: async_scoped_session):
    result = await session.execute(select(Group).order_by(Group.platform_id))
    obj = result.scalars().all()

    group_map = {}
    for item in obj:
        group_map.setdefault(str(item.platform_id), []).append(str(item.bot_qq))

    if not group_map:
        output = "当前未添加任何群"
    else:
        lines = []
        for group_id in sorted(group_map.keys()):
            bot_list = group_map[group_id]
            bots = ", ".join(sorted(set(bot_list)))
            lines.append(f"{group_id} -> {bots}")
        output = "群白名单（群号 -> 允许的机器人账号）：\n" + "\n".join(lines)

    await view_whitelist_group.finish(output)


@del_goods_all.handle()
async def handler_del_goods_all(bot: Bot, session: async_scoped_session):
    await session.execute(delete(Goods).where(Goods.bot_qq == bot.self_id))
    await session.commit()
    await del_goods_all.finish(f"已成功删除 {bot.self_id} 下的所有商品记录")
