from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import Match
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .permission import invalidate_admin_cache
from .utils import _valid_qq
from ..command import add_admin, del_admin
from ..model.admin import Admin


@add_admin.handle()
async def handler_add_admin(
        bot: Bot,
        session: async_scoped_session,
        qq: Match[str]
):
    try:
        admin = _valid_qq(str(qq.result))
    except ValueError:
        await add_admin.finish("QQ号不合法")
        return

    try:
        session.add(Admin(bot_qq=bot.self_id, admin_qq=admin))
        await session.commit()
        invalidate_admin_cache(str(bot.self_id), admin)
        await add_admin.finish(f"已设置主人：{admin}")

    except IntegrityError:
        await session.rollback()
        invalidate_admin_cache(str(bot.self_id), admin)
        await add_admin.finish(f"已设置主人：{admin}")


@del_admin.handle()
async def handler_del_admin(
        bot: Bot,
        session: async_scoped_session,
        qq: Match[str]
):
    try:
        admin = _valid_qq(str(qq.result))
    except ValueError:
        await del_admin.finish("QQ号不合法")
        return

    try:
        stmt = (
            select(Admin)
            .where(
                Admin.bot_qq == bot.self_id,
                Admin.admin_qq == admin
            )
        )
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()

        if obj is not None:
            await session.delete(obj)
            await session.commit()
            invalidate_admin_cache(str(bot.self_id), admin)

        await del_admin.finish("已取消设置该主人")

    except SQLAlchemyError:
        await session.rollback()
        await del_admin.finish("数据库错误，取消失败")
