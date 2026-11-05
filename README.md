<h1 align="center">MultiEcho-Candy</h1>

<p align="center">
  可拓展的多账号 QQ 群消息复读机器人
</p>

<p align="center">
  <a href="https://github.com/BoolCox/MultiEcho/issues"><img src="https://img.shields.io/github/issues/BoolCox/MultiEcho?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/BoolCox/MultiEcho/blob/master/LICENSE"><img src="https://img.shields.io/github/license/BoolCox/MultiEcho?style=flat-square" alt="License"></a>
  <a href="https://dotnet.microsoft.com"><img src="https://img.shields.io/badge/.NET-10.0-purple?style=flat-square" alt=".NET"></a>
  <a href="https://nonebot.dev"><img src="https://img.shields.io/badge/NoneBot-2-red?style=flat-square" alt="NoneBot2"></a>
</p>

---

## ✨ 功能特性

| 特性 | 说明 |
|------|------|
| 🤖 多账号管理 | 同时运行多个 NapCat 实例，每个实例独立登录不同账号 |
| 🔁 自动回复 | 当群内有人发送 `类型/代号/费用` 格式的消息时，机器人自动回复 `@发送者 费用` |
| 🔐 权限体系 | 超级管理员 / 管理员两级权限，灵活管控 |
| 🧩 按账号隔离 | 管理员、群白名单、商品列表、延迟均按机器人账号独立存储 |
| ⏱️ 可调延迟 | 支持为回复设置 0 ~ 30000 ms 的延迟 |

> 📖 详细的命令列表与使用流程请查看 [Bot 使用说明](./multi_echo/docs/multi_echo_usage.md)

---

## 🏗️ 技术架构

本项目由三个部分协同工作：

```mermaid
graph LR
    Launcher["🚀 Launcher<br/>.NET 10 AOT"]
    NoneBot["🤖 NoneBot2<br/>multi_echo 插件"]
    NapCat1["💬 NapCat ①"]
    NapCat2["💬 NapCat ②"]
    NapCatN["💬 NapCat ⋯"]

    Launcher -- "启动 & uv sync" --> NoneBot
    Launcher -- "启动" --> NapCat1
    Launcher -- "启动 & 符号链接 config" --> NapCat2
    Launcher -- "启动 & 符号链接 config" --> NapCatN
    NapCat1 -- "WebSocket" --> NoneBot
    NapCat2 -- "WebSocket" --> NoneBot
    NapCatN -- "WebSocket" --> NoneBot
```

> **Launcher 的职责：**
> 1. 配置 `nonebot` 和所有 `napcat*` 。
> 2. 启动并管理 NoneBot 进程和所有 NapCat 实例、监控运行状态。
> 3. 自动z NapCat 的 WebUI 地址并在浏览器中打开，方便登录。

---

## 📁 项目结构

```
MultiEcho/
├── Launcher/               # 启动器
│   ├── Launcher.slnx
│   ├── Launcher.csproj
│   └── app.manifest
├── multi_echo/             # NoneBot2 插件
│   ├── pyproject.toml
│   ├── src/plugins/        # 插件源码
│   └── docs/               # 使用说明
├── build/                  # 构建产物输出
└── README.md
```

---

## 🚀 用户指南

### 1. 下载程序

1. 前往 [Releases 页面](https://github.com/BoolCox/MultiEcho/releases/tag/1.0.0) 下载最新的压缩包。
2. 将压缩包解压到任意目录。

### 2. 安装依赖 & 配置

1. 安装 [uv](https://github.com/astral-sh/uv)（Python 包管理器）。
2. 将 `nonebot/.env.multi_echo_candy.example` 重命名为 `nonebot/.env.multi_echo_candy`。
3. 打开 `nonebot/.env.multi_echo_candy`，将 `SUPERUSERS` 设置为你（以及需要一起管理的人）的 QQ 号，可填多个，用英文逗号分隔：

   ```
   SUPERUSERS=["123456789", "987654321"]
   ```

### 3. 启动程序

1. 双击 `Launcher.exe`。
2. 在弹出的浏览器页面上登录账号。

> **提示**
> - 如果启动程序显示 `waiting` 字样，可关闭后重新打开。
> - 若启动程序卡住，按一下回车即可恢复。

### 4. 多账号启动

如需同时登录多个账号：

1. 复制安装目录中任意一个 `napcat` 文件夹，重命名为 `napcat2`（或 `napcat3`、`napcat10` 等）。
2. 重新启动 `Launcher.exe`，程序会自动配置新的 `napcat*` 。
3. ⚠️ **不要**在"系统配置 → 登录配置"里设置快速登录，以避免所有实例登录同一个账号。

### 5. 账号风控与重登

如果账号被风控需要重新登录：

- 在对应网页的 **系统配置 → 登录配置** 中点击 **重启进程**，刷新网页即可重新登录。

---

## 🛠️ 开发者构建指南

### 环境要求

| 工具 | 版本要求 |
|------|---------|
| [.NET SDK](https://dotnet.microsoft.com/download) | 10.0 或更高 |
| [uv](https://github.com/astral-sh/uv) | 最新版 |
| Python | ≥ 3.10, < 4.0 |
| 操作系统 | 默认 Windows x64（可在 `Launcher.csproj` 中修改 `RuntimeIdentifier`） |

### 构建步骤

```bash
git clone https://github.com/BoolCox/MultiEcho.git
cd MultiEcho
dotnet publish Launcher/Launcher.csproj -c Release
```

`dotnet publish` 会自动完成 AOT 编译并组装 `build/` 目录（Launcher + NoneBot 插件 + NapCat 下载解压 + 网络配置生成），构建完成后将 `build/` 目录整体分发即可使用。

### 开发 NoneBot 插件

```bash
cd multi_echo
uv sync                # 安装依赖
uv sync --extra dev    # 安装开发依赖（pyright、ruff）
```

### 自定义 NapCat 版本

在 `Launcher/Launcher.csproj` 中修改 `NapcatVersion` 属性：

```xml
<NapcatVersion>v4.16.0</NapcatVersion>
```

---

## 💬 问题反馈

遇到 Bug 或有功能建议？欢迎 [提交 Issue](https://github.com/BoolCox/MultiEcho/issues/new)。
