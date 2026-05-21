from nonebot_plugin_orm import Model
from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class Group(Model):
    """群登记表"""
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), comment="Bot QQ账号")
    platform_id: Mapped[str] = mapped_column(String(64), comment="QQ群号")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")
    random_prefix_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否开启群随机前缀"
    )

    __table_args__ = (
        UniqueConstraint("bot_qq", "platform_id", name="uq_group_bot_qq_platform_id"),
    )
