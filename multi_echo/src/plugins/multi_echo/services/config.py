from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select

from ..model.config import Config


async def get_config_by_key(session: async_scoped_session, key: str) -> Config | None:
    return (
        await session.execute(
            select(Config).where(Config.key == key),
        )
    ).scalar_one_or_none()


async def set_config_by_key(session: async_scoped_session, key: str, value: str) -> None:
    result = await session.get(Config, key)
    if result:
        result.value = value
    else:
        session.add(Config(key=key, value=value))
