from nonebot import get_bots
from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import Event
from nonebot.permission import Permission
from nonebot_plugin_orm import get_session
from sqlalchemy import select

from ..config import EchoConfig
from ..model.admin import Admin

config = get_plugin_config(EchoConfig)


async def is_admin(event: Event) -> bool:
    result = (
        select(Admin)
        .where(
            Admin.bot_qq == event.self_id,
            Admin.admin_qq == event.get_user_id()
        )
    )
    async with get_session() as session:
        found = await session.scalars(result)
        found = found.first()
    return bool(found)


def is_super_admin(event: Event) -> bool:
    """配置文件的管理员和机器人自身都属于超级管理员"""
    try:
        user_id = event.get_user_id()
    except ValueError:
        return True

    if user_id == str(config.superuser) or is_bot(event):
        return True
    else:
        return False


def is_bot(event: Event) -> bool:
    bots = get_bots()
    for bot in bots.values():
        if bot.self_id == event.get_user_id():
            return True
    return False


async def is_admin_or_super_admin(event: Event) -> bool:
    if is_super_admin(event):
        return True
    return await is_admin(event)


ADMIN = Permission(is_admin)
SUPER_ADMIN = Permission(is_super_admin)
ADMIN_OR_SUPER_ADMIN = Permission(is_admin_or_super_admin)
