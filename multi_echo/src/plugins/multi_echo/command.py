from arclet.alconna import Alconna, Args, CommandMeta, MultiVar, Arg
from nonebot import on_command, on_message
from nonebot.rule import to_me
from nonebot_plugin_alconna import on_alconna

from .handler.permission import (
    ADMIN_OR_SUPER_ADMIN_OR_SELF,
    SUPER_ADMIN,
    SUPER_ADMIN_OR_SELF,
)

# 1. 管理员管理（仅超级管理员或机器人自身）
add_admin = on_alconna(
    Alconna("添加主人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

del_admin = on_alconna(
    Alconna("删除主人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

# 2. 群管理
add_group = on_alconna(
    Alconna("添加群", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

del_group = on_alconna(
    Alconna("删除群", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

add_blocked_user = on_alconna(
    Alconna("添加屏蔽人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

del_blocked_user = on_alconna(
    Alconna("删除屏蔽人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

# 3. 商品管理（仅配置文件的超级管理员 SUPERUSER 可操作，机器人自身和主人均不可操作）
set_goods = on_alconna(
    Alconna(
        "设置压车数",
        Arg("goods_list", MultiVar(str), seps="/"),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=SUPER_ADMIN,
    priority=5,
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
    permission=SUPER_ADMIN,
    priority=5,
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
    permission=SUPER_ADMIN,
    priority=5,
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
    permission=SUPER_ADMIN,
    priority=5,
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
    permission=SUPER_ADMIN,
    priority=5,
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
    permission=SUPER_ADMIN,
    priority=5,
    block=True
)

set_min_price = on_alconna(
    Alconna(
        "设置下限",
        Args(
            Arg("group", int),
            Arg("min_price", int),
            separators="#"
        ),
        meta=CommandMeta(compact=True)
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=SUPER_ADMIN,
    priority=5,
    block=True
)

del_goods_all = on_alconna(
    Alconna("清空商品"),
    skip_for_unmatch=False,
    response_self=True,
    permission=SUPER_ADMIN,
    priority=5,
    block=True
)

# 4. 开关与状态（需 @机器人）
total_switch = on_command(
    "切换总开关",
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

view_status = on_command(
    "查看状态",
    rule=to_me(),
    aliases={"查看跟随状态"},
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

view_whitelist_group = on_command(
    "查看群列表",
    rule=to_me(),
    aliases={"查看当前添加群"},
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

set_delay = on_alconna(
    Alconna("设置群延迟", Args["args?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

set_group_random_reply = on_alconna(
    Alconna(
        "设置群随机回复",
        Args(
            Arg("group_id", str),
            Arg("random_reduce_limit", int),
            separators="#"
        ),
        meta=CommandMeta(compact=True),
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

open_random_prefix = on_alconna(
    Alconna(
        "开启群压车符号",
        Args["group", str],
        meta=CommandMeta(compact=True),
        separators="#"
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

disable_random_prefix = on_alconna(
    Alconna(
        "关闭群压车符号",
        Args["group", str],
        meta=CommandMeta(compact=True),
        separators="#"
    ),
    skip_for_unmatch=False,
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

# 5. 随机回复群开关
switch_group_random_reply = on_alconna(
    Alconna(
        "切换随机回复群开关",
        Args["group_id?", str],
        meta=CommandMeta(compact=True)
    ),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    priority=5,
    block=True
)

# 核心功能（最高优先级，避免被管理命令的权限检查和解析阻塞）
echo = on_message(priority=1, block=False)
