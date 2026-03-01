from nonebot_plugin_orm import Model
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class Admin(Model):
    """管理员表"""
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), comment="Bot QQ号")
    admin_qq: Mapped[str] = mapped_column(String(64), comment="管理员QQ号")

    __table_args__ = (
        UniqueConstraint("bot_qq", "admin_qq", name="uq_admin_bot_qq_admin_qq"),
    )
