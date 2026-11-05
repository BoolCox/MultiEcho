from nonebot import require
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import add_global_extension
from nonebot_plugin_alconna.builtins.extensions.onebot11 import MessageSentExtension

from . import handler
from . import model

require("nonebot_plugin_orm")
require("nonebot_plugin_alconna")
add_global_extension(MessageSentExtension())

__plugin_meta__ = PluginMetadata(
    name="multi_echo",
    description="用多个账号复读指定用户的消息",
    usage="",
)
