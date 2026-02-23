from arclet.alconna import Alconna, Args, CommandMeta, MultiVar, Arg
from nonebot import on_command, on_message
from nonebot.rule import to_me
from nonebot_plugin_alconna import on_alconna

from .handler.permission import SUPER_ADMIN, ADMIN_OR_SUPER_ADMIN

# 1. 管理员管理（仅超级管理员）
add_admin = on_alconna(
    Alconna("添加主人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN,
    block=True
)

del_admin = on_alconna(
    Alconna("删除主人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN,
    block=True
)

# 2. 白名单管理
add_group = on_alconna(
    Alconna("添加群", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

del_group = on_alconna(
    Alconna("删除群", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

add_blocked_user = on_alconna(
    Alconna("添加屏蔽人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN,
    block=True
)

del_blocked_user = on_alconna(
    Alconna("删除屏蔽人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN,
    block=True
)

# 3 商品管理
set_goods = on_alconna(
    Alconna(
        "设置压车数",
        Arg("goods_list", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

del_goods = on_alconna(
    Alconna(
        "删除压车数",
        Arg("goods_list", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

set_rand_three_tail_three_pack_goods = on_alconna(
    Alconna(
        "设置随机三尾三包压车数",
        Arg("goods_range", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

del_rand_three_tail_three_pack_goods = on_alconna(
    Alconna(
        "删除随机三尾三包压车数",
        Arg("goods_range", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

set_onepack_goods = on_alconna(
    Alconna(
        "设置一包杀压车数",
        Arg("goods_list", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

del_onepack_goods = on_alconna(
    Alconna(
        "删除一包杀压车数",
        Arg("goods_list", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True)
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

set_min_price = on_alconna(
    Alconna(
        "设置下限",
        Args["min_price", int],
        meta=CommandMeta(compact=True)
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

del_goods_all = on_alconna(
    Alconna("清空商品"),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

# 4. 开关与状态（需 @机器人）
total_switch = on_command(
    "切换总开关",
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

view_status = on_command(
    "查看状态",
    rule=to_me(),
    aliases={"查看跟随状态"},
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

view_whitelist_group = on_command(
    "查看当前添加群",
    rule=to_me(),
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

set_delay = on_alconna(
    Alconna("设置群延迟", Args["args?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

set_group_random_reply = on_alconna(
    Alconna(
        "设置群随机回复",
        Args(
            Arg("group_id", str),
            Arg("count", int),
            separators="#"
        ),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

# 4. 随机回复群开关
switch_group_random_reply = on_alconna(
    Alconna(
        "切换随机回复群开关",
        Args["group_id?", str],
        meta=CommandMeta(compact=True)
    ),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN,
    block=True
)

# 核心功能
echo = on_message(priority=20)
