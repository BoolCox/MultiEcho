from nonebot_plugin_orm import Model
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class Delay(Model):
    __tablename__ = "delays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), index=True)
    group_id: Mapped[str] = mapped_column(String(64))
    delay: Mapped[int] = mapped_column(Integer, default=0)
