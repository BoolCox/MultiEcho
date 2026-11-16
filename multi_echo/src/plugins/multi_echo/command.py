from arclet.alconna import Alconna, Args, CommandMeta
from nonebot import on_command, on_message
from nonebot.rule import to_me
from nonebot_plugin_alconna import on_alconna

from .handler.permission import (
    ADMIN_OR_SUPER_ADMIN_OR_SELF,
    SUPER_ADMIN_OR_SELF,
)

# 1. 管理员管理（仅超级管理员或机器人自身）
add_admin = on_alconna(
    Alconna("添加主人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN_OR_SELF,
    block=True
)

del_admin = on_alconna(
    Alconna("删除主人", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=SUPER_ADMIN_OR_SELF,
    block=True
)

# 2. 白名单管理
add_group = on_alconna(
    Alconna("添加群", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

del_group = on_alconna(
    Alconna("删除群", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

# 3. 跟随管理
follow_user = on_alconna(
    Alconna("跟随", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

unfollow_user = on_alconna(
    Alconna("取消跟随", Args["qq?", str], meta=CommandMeta(compact=True)),
    response_self=True,
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

# 4. 开关与状态（需 @机器人）
follow_switch = on_command(
    "切换跟随总开关",
    rule=to_me(),
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

view_status = on_command(
    "查看状态",
    rule=to_me(),
    aliases={"查看跟随状态"},
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

view_whitelist_group = on_command(
    "查看当前添加群",
    rule=to_me(),
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

# 5. 延迟设置（需 @机器人）
set_delay = on_command(
    "设置跟随延迟",
    rule=to_me(),
    permission=ADMIN_OR_SUPER_ADMIN_OR_SELF,
    block=True
)

# 核心功能
echo = on_message(priority=20)
