from enum import Enum

from nonebot_plugin_orm import Model
from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class GoodsType(Enum):
    NORMAL = "normal"  # 普通商品
    ONEPACK = "onepack"  # 一包杀
    RAND_THREE_TAIL_THREE_PACK = "rand_three_tail_three_pack"  # 随机三尾三包
    # 可扩展更多类型


class Goods(Model):
    """商品目录表"""
    __tablename__ = "goods"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_qq: Mapped[str] = mapped_column(String(64), comment="Bot QQ号")
    code: Mapped[str] = mapped_column(String(64), comment="商品代号")
    max_price: Mapped[int] = mapped_column(Integer, comment="费用上限")
    min_price: Mapped[int] = mapped_column(Integer, default=0, comment="费用下限")
    goods_type: Mapped[str] = mapped_column(String(32), default=GoodsType.NORMAL.value, comment="商品类型")

    __table_args__ = (
        UniqueConstraint("bot_qq", "code", "goods_type", name="uq_goods_bot_qq_code_type"),
    )
