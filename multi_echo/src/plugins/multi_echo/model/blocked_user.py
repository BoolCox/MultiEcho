from nonebot_plugin_orm import Model
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class BlockedUser(Model):
    """屏蔽用户表"""

    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), comment="Bot QQ号")
    user_qq: Mapped[str] = mapped_column(String(64), comment="被屏蔽用户QQ号")

    __table_args__ = (
        UniqueConstraint("bot_qq", "user_qq", name="uq_blocked_bot_qq_user_qq"),
    )
