from nonebot import get_bot
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot_plugin_orm import async_scoped_session

from .cache import invalidate_total_switch_cache
from ..command import total_switch
from ..model.total_switch import TotalSwitch


@total_switch.handle()
async def handler_total_switch(bot: Bot, session: async_scoped_session):
    """处理总开关的命令"""
    frist_bot = get_bot()
    if bot.self_id != frist_bot.self_id:
        return

    obj = await session.get(TotalSwitch, 1)
    if obj is None:
        obj = TotalSwitch(id=1, enabled=True)
        session.add(obj)
        new_status = True
    else:
        obj.enabled = not obj.enabled
        new_status = obj.enabled

    await session.commit()
    invalidate_total_switch_cache()

    await total_switch.finish(
        "已开启总开关" if new_status else "已关闭总开关"
    )
