from nonebot_plugin_orm import Model
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

class GroupRandomReply(Model):
    __tablename__ = "group_random_reply"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), index=True)
    group_id: Mapped[str] = mapped_column(String(64), index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)  # 新增，默认关闭
