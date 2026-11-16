from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Event
from nonebot.permission import Permission
from nonebot_plugin_orm import get_session
from sqlalchemy import select

from ..model.admin import Admin


def _get_user_id(event: Event) -> str | None:
    try:
        return event.get_user_id()
    except ValueError:
        user_id = getattr(event, "user_id", None)
        return str(user_id) if user_id is not None else None


def is_self(event: Event) -> bool:
    user_id = _get_user_id(event)
    return user_id is not None and str(event.self_id) == user_id


async def is_admin(event: Event) -> bool:
    user_id = _get_user_id(event)
    if user_id is None:
        return False

    result = (
        select(Admin)
        .where(
            Admin.bot_qq == str(event.self_id),
            Admin.admin_qq == user_id
        )
    )
    async with get_session() as session:
        found = await session.scalars(result)
        return found.first() is not None


async def is_super_admin(event: Event) -> bool:
    """NoneBot 配置 `SUPERUSERS` 中的超级管理员。"""
    user_id = _get_user_id(event)
    return user_id is not None and user_id in get_driver().config.superusers


async def is_super_admin_or_self(event: Event) -> bool:
    """超级管理员和机器人自身都可以管理当前机器人账号。"""
    return await is_super_admin(event) or is_self(event)


async def is_admin_or_super_admin_or_self(event: Event) -> bool:
    if await is_super_admin_or_self(event):
        return True
    return await is_admin(event)


ADMIN = Permission(is_admin)
SUPER_ADMIN = Permission(is_super_admin)
SUPER_ADMIN_OR_SELF = Permission(is_super_admin_or_self)
ADMIN_OR_SUPER_ADMIN_OR_SELF = Permission(is_admin_or_super_admin_or_self)
