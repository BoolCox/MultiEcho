from nonebot.adapters.onebot.v11.bot import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from .cache import invalidate_delay_cache
from ..command import set_delay
from ..model.delay import Delay


@set_delay.handle()
async def handler_set_delay(bot: Bot, session: async_scoped_session, args: Match[str]):
    arg = str(args.result).strip()
    lines = arg.split("#")
    if len(lines) != 2:
        await set_delay.finish("请输入正确格式：<群号>#<延迟毫秒>")
    group_id, delay_line = lines
    group_id = group_id.strip()
    delay_str = delay_line.strip()
    if not group_id.isdigit():
        await set_delay.finish("群号必须为数字")
    if not delay_str.isdigit():
        await set_delay.finish("延迟必须为0~30000之间的整数（毫秒）")
    delay = int(delay_str)
    if not (0 <= delay <= 30000):
        await set_delay.finish("延迟必须在0~30000毫秒之间")

    bot_id = bot.self_id
    res = await session.execute(select(Delay).where(Delay.bot_qq == bot_id, Delay.group_id == group_id))
    obj = res.scalar_one_or_none()
    if obj:
        obj.delay = delay
    else:
        obj = Delay(bot_qq=bot_id, group_id=group_id, delay=delay)
        session.add(obj)

    await session.commit()
    invalidate_delay_cache(str(bot_id), group_id)
    await set_delay.finish(f"已将该群的回复延迟设置为 {delay} 毫秒")
