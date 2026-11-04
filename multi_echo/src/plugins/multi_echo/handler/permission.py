from cachetools import TTLCache
from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import Event
from nonebot.permission import Permission
from nonebot_plugin_orm import get_session
from sqlalchemy import select

from ..config import EchoConfig
from ..model.admin import Admin

config = get_plugin_config(EchoConfig)

admin_cache = TTLCache(maxsize=1024, ttl=300)


def invalidate_admin_cache(bot_qq: str, admin_qq: str) -> None:
    admin_cache.pop(f"{bot_qq}:{admin_qq}", None)


def _get_user_id(event: Event) -> str | None:
    try:
        return event.get_user_id()
    except ValueError:
        user_id = getattr(event, "user_id", None)
        return str(user_id) if user_id is not None else None


def is_self(event: Event) -> bool:
    user_id = _get_user_id(event)
    return user_id is not None and str(event.self_id) == user_id


async def is_super_admin(event: Event) -> bool:
    """仅配置文件的超级管理员（不包含机器人自身和普通主人）"""
    user_id = _get_user_id(event)
    return user_id is not None and user_id == str(config.superuser)


async def is_admin(event: Event) -> bool:
    user_qq = _get_user_id(event)
    if user_qq is None:
        return False

    bot_qq = str(event.self_id)
    cache_key = f"{bot_qq}:{user_qq}"
    if cache_key in admin_cache:
        return admin_cache[cache_key]

    result = (
        select(Admin)
        .where(
            Admin.bot_qq == bot_qq,
            Admin.admin_qq == user_qq
        )
    )
    async with get_session() as session:
        found = await session.scalars(result)
        is_found = bool(found.first())

    admin_cache[cache_key] = is_found
    return is_found


async def is_super_admin_or_self(event: Event) -> bool:
    """配置文件的管理员和机器人自身都属于超级管理员"""
    return await is_super_admin(event) or is_self(event)


async def is_admin_or_super_admin_or_self(event: Event) -> bool:
    if await is_super_admin_or_self(event):
        return True
    return await is_admin(event)


ADMIN = Permission(is_admin)
SUPER_ADMIN = Permission(is_super_admin)
SUPER_ADMIN_OR_SELF = Permission(is_super_admin_or_self)
ADMIN_OR_SUPER_ADMIN_OR_SELF = Permission(is_admin_or_super_admin_or_self)
