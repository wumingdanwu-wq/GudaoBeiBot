import os
import time
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

# 核心链接配置（方便统一维护）
CHANNEL_URL = "https://t.me/gudaobei_news"
BLOG_URL = "https://zidane.us.ci/"
PROJECT_URL = "https://landscape.zidane.us.ci/"
GITHUB_URL = "https://github.com/wumingdanwu-wq"


# ================= 1. 启动自动注册左下角快捷菜单 =================
async def post_init(application: Application):
    """机器人启动时自动设置聊天框左下角的指令菜单"""
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
    print("✅ 快捷指令菜单已自动注册")


# ================= 2. 核心指令处理函数 =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📢 订阅频道：古道北技术动态", url=CHANNEL_URL),
        ],
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

后续将支持：
🤖 AI问答 | 🛠 技术工具

👇 点击下方按钮快速访问："""

    await update.message.reply_text(text, reply_markup=reply_markup)


async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """推广频道的专属指令"""
    keyboard = [
        [InlineKeyboardButton("📢 立即订阅：古道北技术动态", url=CHANNEL_URL)]
    ]
    text = f"""📢 **古道北技术动态**

这里第一时间推送：
📝 Hugo 博客最新文章
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
/help 查看帮助

💡 提示：在聊天中发送“频道”、“博客”、“景观”、“我的id”可触发自动回复！"""

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
    keyboard = [
        [InlineKeyboardButton("📢 关注频道：古道北技术动态", url=CHANNEL_URL)]
    ]
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
    """查询用户 ID 和当前群组/会话 ID"""
    user = update.effective_user
    chat = update.effective_chat
    text = (
        f"🆔 **ID 信息查询**\n\n"
        f"👤 你的名字：{user.first_name}\n"
        f"🔢 你的 User ID：`{user.id}`\n"
        f"💬 当前会话 ID：`{chat.id}`\n"
        f"🏷 会话类型：`{chat.type}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ================= 3. 实时网站状态检测工具 =================
async def check_sites_status() -> str:
    """使用 httpx 实时检测博客和项目网站状态与响应延迟"""
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

    results.append("\n当前版本：v1.2")
    return "\n".join(results)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📡 正在实时检测各项服务状态，请稍候...")
    report = await check_sites_status()
    await msg.edit_text(report)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理消息底部内联按钮的点击回调"""
    query = update.callback_query
    await query.answer()

    if query.data == "check_status":
        await query.edit_message_text("📡 正在实时检测各项服务状态，请稍候...")
        report = await check_sites_status()
        await query.edit_message_text(report)


# ================= 4. 新成员入群欢迎功能（附带频道推广） =================
def extract_status_change(chat_member_update: ChatMemberUpdated):
    """判断成员是否刚刚加入群组"""
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

        # 欢迎语底部按钮：第一行主推频道，第二行推博客和项目
        keyboard = [
            [
                InlineKeyboardButton("📢 订阅频道：古道北技术动态", url=CHANNEL_URL),
            ],
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


# ================= 5. 关键词智能触发回复 =================
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


# ================= 6. 主程序入口 =================
def main():
    if not TOKEN:
        print("❌ 错误：未读取到 BOT_TOKEN，请检查同级目录下的 .env 文件！")
        return

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # 注册命令处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("channel", channel))
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

    # 注册关键词自动回复处理器（仅监听非命令的普通文本）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_reply))

    print("🚀 古道北助手 v1.2 启动成功！按 Ctrl+C 停止运行。")

    # 开启所有事件监听
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()