import os
import re
import time
import asyncio
import xml.etree.ElementTree as ET
import httpx
from dotenv import load_dotenv

from telegram import (
    Update,
    ChatMember,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# 读取 .env 文件
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
# 读取管理员 User ID（支持在 .env 中配置 ADMIN_ID=123456789）
ADMIN_ID_STR = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR.isdigit() else None

# ================= 核心配置区 =================
CHANNEL_USERNAME = "@gudaobei_news"  # 你的频道用户名（机器人需设为频道管理员）
CHANNEL_URL = "https://t.me/gudaobei_news"
BLOG_URL = "https://zidane.us.ci/"
BLOG_RSS_URL = "https://zidane.us.ci/index.xml"  # Hugo 默认生成的 RSS 地址
PROJECT_URL = "https://landscape.zidane.us.ci/"
GITHUB_URL = "https://github.com/wumingdanwu-wq"

# 记录上一次推送的博客文章链接，避免重复推送
LAST_POST_FILE = "last_post.txt"
CHECK_INTERVAL = 600  # 自动检查博客更新的间隔时间（秒），600秒 = 10分钟


# ================= 权限校验辅助函数 =================
def is_admin(update: Update) -> bool:
    """检查当前发送指令的用户是否为管理员本人"""
    if ADMIN_ID is None:
        return False
    return update.effective_user and update.effective_user.id == ADMIN_ID


# ================= 1. 博客 RSS 解析与自动同步 =================
async def fetch_latest_blog_post():
    """抓取 Hugo 博客 RSS 源中的最新一篇文章"""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(BLOG_RSS_URL)
        resp.raise_for_status()

    root = ET.fromstring(resp.text)

    item = root.find(".//item")
    if item is not None:
        title = item.findtext("title", "新文章发布").strip()
        link = item.findtext("link", BLOG_URL).strip()
        desc = item.findtext("description", "").strip()
        clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
        if len(clean_desc) > 120:
            clean_desc = clean_desc[:120] + "..."
        return {"title": title, "link": link, "summary": clean_desc}

    return None


def get_last_pushed_link() -> str:
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_last_pushed_link(link: str):
    with open(LAST_POST_FILE, "w", encoding="utf-8") as f:
        f.write(link.strip())


async def send_post_to_channel(bot, post: dict):
    """将博客文章排版后发送到频道"""
    keyboard = [
        [InlineKeyboardButton("📖 阅读全文", url=post["link"])],
        [
            InlineKeyboardButton("📚 古道北博客", url=BLOG_URL),
            InlineKeyboardButton("🌿 古道景观设计", url=PROJECT_URL),
        ],
    ]
    summary_part = f"\n\n📝 摘要：\n{post['summary']}" if post["summary"] else ""
    text = (
        f"📢 **古道北博客更新啦！**\n\n"
        f"📌 **{post['title']}**"
        f"{summary_part}\n\n"
        f"🔗 原文链接：\n{post['link']}"
    )
    await bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def auto_check_blog_loop(application: Application):
    """后台定时任务：自动检测 Hugo 博客是否有新文章"""
    await asyncio.sleep(5)
    print("🔄 博客 RSS 自动监测任务已启动（每 10 分钟检查一次）")

    if not get_last_pushed_link():
        try:
            latest = await fetch_latest_blog_post()
            if latest:
                save_last_pushed_link(latest["link"])
                print(f"📌 已记录当前最新博客文章：{latest['title']}")
        except Exception as e:
            print(f"⚠️ 首次读取博客 RSS 失败（稍后将自动重试）: {e}")

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            latest = await fetch_latest_blog_post()
            if latest:
                last_link = get_last_pushed_link()
                if latest["link"] != last_link:
                    await send_post_to_channel(application.bot, latest)
                    save_last_pushed_link(latest["link"])
                    print(f"✅ 已自动同步新博客文章到频道：{latest['title']}")
        except Exception as e:
            print(f"⚠️ 自动检查博客更新时出错: {e}")


# ================= 2. 频道广播与手动同步指令（仅限管理员） =================
async def broadcast_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """指令：/post 内容 -> 仅管理员可往频道发送广播"""
    if ADMIN_ID is None:
        await update.message.reply_text(
            "⚠️ 尚未配置管理员权限！\n"
            "请先用大号发送 `/id` 获取你的 User ID，然后在 `.env` 文件中添加：\n"
            "`ADMIN_ID=你的User_ID` 并重启机器人。",
            parse_mode="Markdown",
        )
        return

    if not is_admin(update):
        await update.message.reply_text("⛔ 权限不足：此指令仅限古道北管理员使用！")
        return

    if not context.args:
        await update.message.reply_text(
            "💡 **广播功能用法（管理员专属）**：\n"
            "请在 `/post` 后面加上空格和你要广播的内容，例如：\n\n"
            "`/post 大家好，古道北技术动态频道正式开通！`",
            parse_mode="Markdown",
        )
        return

    content = " ".join(context.args)
    keyboard = [
        [
            InlineKeyboardButton("📚 古道北博客", url=BLOG_URL),
            InlineKeyboardButton("🌿 古道景观设计", url=PROJECT_URL),
        ]
    ]
    text = f"📢 **古道北动态通知**\n\n{content}"

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        await update.message.reply_text(f"✅ 广播已成功发送到频道 {CHANNEL_USERNAME}！")
    except Exception as e:
        await update.message.reply_text(
            f"❌ 发送失败：{e}\n\n"
            f"请检查是否已将机器人添加为频道 {CHANNEL_USERNAME} 的管理员，并开启了「发布消息」权限！"
        )


async def sync_blog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """指令：/sync -> 仅管理员可手动触发博客同步"""
    if ADMIN_ID is None:
        await update.message.reply_text(
            "⚠️ 尚未配置管理员权限！请先在 `.env` 文件中设置 `ADMIN_ID`。",
            parse_mode="Markdown",
        )
        return

    if not is_admin(update):
        await update.message.reply_text("⛔ 权限不足：此指令仅限古道北管理员使用！")
        return

    msg = await update.message.reply_text("🔄 正在读取古道北博客最新文章并推送到频道...")
    try:
        latest = await fetch_latest_blog_post()
        if not latest:
            await msg.edit_text("⚠️ 未能在 RSS 源中找到文章，请确认 https://zidane.us.ci/index.xml 是否可访问。")
            return

        await send_post_to_channel(context.bot, latest)
        save_last_pushed_link(latest["link"])
        await msg.edit_text(
            f"✅ **同步成功！**\n\n已将最新文章《{latest['title']}》推送至频道 {CHANNEL_USERNAME}！",
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ 推送失败：{e}\n\n"
            f"1. 请确认机器人已是频道 {CHANNEL_USERNAME} 的管理员。\n"
            f"2. 请确认博客 RSS 地址 {BLOG_RSS_URL} 可以正常打开。"
        )


# ================= 3. 启动自动注册左下角快捷菜单（隐藏管理指令） =================
async def post_init(application: Application):
    """机器人启动时自动设置公开指令菜单（不包含 /post 和 /sync）"""
    commands = [
        BotCommand("start", "👋 开始使用"),
        BotCommand("channel", "📢 订阅古道北技术动态"),
        BotCommand("blog", "📝 访问古道北博客"),
        BotCommand("project", "🌿 查看景观设计项目"),
        BotCommand("status", "📡 实时检测网站状态"),
        BotCommand("github", "💻 GitHub 开源项目"),
        BotCommand("about", "👤 关于古道北"),
        BotCommand("id", "🆔 查询当前用户与群组ID"),
        BotCommand("contact", "📮 联系方式"),
        BotCommand("help", "📚 查看帮助"),
    ]
    await application.bot.set_my_commands(commands)
    print("✅ 快捷指令菜单已自动注册（已隐藏管理员指令）")

    if ADMIN_ID:
        print(f"🔐 管理员权限已锁定 User ID: {ADMIN_ID}")
    else:
        print("⚠️ 警告：未在 .env 中检测到 ADMIN_ID，请尽快配置以启用 /post 和 /sync！")

    # 启动后台博客更新自动检测任务
    asyncio.create_task(auto_check_blog_loop(application))


# ================= 4. 基础公开指令处理函数 =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 订阅频道：古道北技术动态", url=CHANNEL_URL)],
        [
            InlineKeyboardButton("📚 古道北博客", url=BLOG_URL),
            InlineKeyboardButton("🌿 古道景观设计", url=PROJECT_URL),
        ],
        [
            InlineKeyboardButton("💻 GitHub 主页", url=GITHUB_URL),
            InlineKeyboardButton("📡 实时网站测速", callback_data="check_status"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"""👋 欢迎来到古道北助手

我是古道北的个人技术助手。

📢 官方频道（最新技术与博客动态）：
{CHANNEL_URL}

目前功能：
/channel 订阅技术动态频道
/blog 查看博客
/project 查看项目
/status 实时网站状态检测
/id 查询个人与群组ID
/help 查看全部帮助

👇 点击下方按钮快速访问："""

    await update.message.reply_text(text, reply_markup=reply_markup)


async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📢 立即订阅：古道北技术动态", url=CHANNEL_URL)]]
    text = f"""📢 **古道北技术动态**

这里第一时间推送：
📝 Hugo 博客最新文章自动同步
🤖 AI 工具与探索实践
💻 GitHub 开源项目更新
🌐 网络与 Linux 折腾笔记

频道地址：
{CHANNEL_URL}

👇 点击下方按钮一键订阅，不错过任何更新！"""

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📚 古道北助手帮助

/start 开始使用
/channel 订阅「古道北技术动态」频道
/blog 查看博客
/project 查看项目
/about 关于我
/github GitHub项目
/status 实时系统状态检测
/id 查询用户与群组ID
/contact 联系方式
/help 查看帮助"""

    # 如果是管理员本人查看帮助，额外展示隐藏的管理指令
    if is_admin(update):
        text += (
            "\n\n🔐 **管理员专属指令（仅你可见）**：\n"
            "/post <内容> - 发送广播通知到频道\n"
            "/sync - 手动同步最新博客到频道"
        )

    await update.message.reply_text(text)


async def blog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👉 点击进入古道北博客", url=BLOG_URL)],
        [InlineKeyboardButton("📢 订阅频道获取更新通知", url=CHANNEL_URL)],
    ]
    await update.message.reply_text(
        f"📝 古道北博客：\n{BLOG_URL}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌿 打开古道景观设计", url=PROJECT_URL)],
        [InlineKeyboardButton("📢 关注古道北技术动态", url=CHANNEL_URL)],
    ]
    await update.message.reply_text(
        f"我的项目：\n\n🌿 古道景观设计\n{PROJECT_URL}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📢 关注频道：古道北技术动态", url=CHANNEL_URL)]]
    text = f"""👤 关于古道北

记录个人学习与折腾历程。

方向：
🌐 网络技术
💻 Linux / VPS
📝 Hugo博客
🤖 AI探索
🌿 项目设计

📢 频道：{CHANNEL_URL}
📝 博客：{BLOG_URL}

欢迎交流学习。"""

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💻 访问 GitHub 主页", url=GITHUB_URL)],
        [InlineKeyboardButton("📢 订阅古道北技术动态", url=CHANNEL_URL)],
    ]
    text = f"""💻 GitHub

主页：
{GITHUB_URL}

我的项目：
📝 Gudaobei-Blog - 博客系统
🌿 landscape-design - 景观设计展示
🤖 GudaoBeiBot - Telegram机器人"""

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 古道北技术动态频道", url=CHANNEL_URL)],
        [InlineKeyboardButton("📝 古道北博客", url=BLOG_URL)],
    ]
    text = f"""📮 联系方式

📢 Telegram 频道：
{CHANNEL_URL}

💻 GitHub：
{GITHUB_URL}

📝 博客：
{BLOG_URL}"""

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    role = "👑 管理员本人" if is_admin(update) else "👤 普通用户"
    text = (
        f"🆔 **ID 信息查询**\n\n"
        f"👤 你的名字：{user.first_name}\n"
        f"🔢 你的 User ID：`{user.id}`\n"
        f"🛡 当前权限：{role}\n"
        f"💬 当前会话 ID：`{chat.id}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ================= 5. 实时网站状态检测工具 =================
async def check_sites_status() -> str:
    sites = {
        "古道北博客": BLOG_URL,
        "古道景观设计": PROJECT_URL,
        "GitHub主页": GITHUB_URL,
    }

    results = ["📡 古道北助手状态\n\n🤖 机器人：✅ 运行中"]

    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        for name, url in sites.items():
            start_time = time.time()
            try:
                resp = await client.get(url)
                latency = int((time.time() - start_time) * 1000)
                if resp.status_code == 200:
                    results.append(f"🌐 {name}：✅ 在线 ({latency}ms)")
                else:
                    results.append(f"🌐 {name}：⚠️ 状态码 {resp.status_code} ({latency}ms)")
            except Exception:
                results.append(f"🌐 {name}：❌ 连接超时或离线")

    results.append("\n当前版本：v1.4 (管理员权限安全版)")
    return "\n".join(results)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📡 正在实时检测各项服务状态，请稍候...")
    report = await check_sites_status()
    await msg.edit_text(report)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_status":
        await query.edit_message_text("📡 正在实时检测各项服务状态，请稍候...")
        report = await check_sites_status()
        await query.edit_message_text(report)


# ================= 6. 新成员入群欢迎功能 =================
def extract_status_change(chat_member_update: ChatMemberUpdated):
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get(
        "is_member", (None, None)
    )

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)

    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result

    if not was_member and is_member:
        user = update.chat_member.new_chat_member.user

        keyboard = [
            [InlineKeyboardButton("📢 订阅频道：古道北技术动态", url=CHANNEL_URL)],
            [
                InlineKeyboardButton("📚 古道北博客", url=BLOG_URL),
                InlineKeyboardButton("🌿 古道景观设计", url=PROJECT_URL),
            ],
        ]

        text = f"""👋 欢迎 {user.first_name} 加入古道北技术交流群！

这里交流：
📚 Hugo博客 | 🤖 AI探索
💻 GitHub项目 | 🌐 网络技术

📢 必看频道（古道北技术动态）：
{CHANNEL_URL}

📝 个人博客：
{BLOG_URL}

👇 点击下方按钮一键订阅频道与访问博客，欢迎交流学习！"""

        await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ================= 7. 关键词智能触发回复 =================
async def keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    if text in ["频道", "动态", "订阅", "通知", "更新"]:
        await channel(update, context)
    elif text in ["博客", "博客地址", "网站"]:
        keyboard = [[InlineKeyboardButton("👉 访问古道北博客", url=BLOG_URL)]]
        await update.message.reply_text(
            f"💡 古道北博客地址：\n{BLOG_URL}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif text in ["项目", "景观", "景观设计"]:
        keyboard = [[InlineKeyboardButton("🌿 查看古道景观设计", url=PROJECT_URL)]]
        await update.message.reply_text(
            f"🌿 古道景观设计展示：\n{PROJECT_URL}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif text in ["我的id", "id", "群id"]:
        await get_id(update, context)


# ================= 8. 主程序入口 =================
def main():
    if not TOKEN:
        print("❌ 错误：未读取到 BOT_TOKEN，请检查同级目录下的 .env 文件！")
        return

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # 注册命令处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("channel", channel))
    app.add_handler(CommandHandler("post", broadcast_post))
    app.add_handler(CommandHandler("sync", sync_blog))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("blog", blog))
    app.add_handler(CommandHandler("project", project))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("github", github))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("id", get_id))

    # 注册按钮点击回调处理器
    app.add_handler(CallbackQueryHandler(button_callback))

    # 注册新成员入群欢迎处理器
    app.add_handler(
        ChatMemberHandler(
            welcome,
            ChatMemberHandler.CHAT_MEMBER,
        )
    )

    # 注册关键词自动回复处理器
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_reply))

    print("🚀 古道北助手 v1.4 启动成功！按 Ctrl+C 停止运行。")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()