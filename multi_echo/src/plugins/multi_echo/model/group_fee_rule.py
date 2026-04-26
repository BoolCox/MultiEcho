from nonebot_plugin_orm import Model
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class GroupFeeRule(Model):
    __tablename__ = "group_fee_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), index=True, comment="Bot QQ账号")
    group_id: Mapped[str] = mapped_column(String(64), index=True, comment="QQ群号")
    min_price: Mapped[int] = mapped_column(Integer)
