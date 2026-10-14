from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

import os
from dotenv import load_dotenv

# 读取 .env 文件
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
👋 欢迎来到古道北助手

我是古道北的个人技术助手。

目前功能：

/help 查看帮助
/blog 查看博客
/project 查看项目

后续将支持：
🤖 AI问答
📢 博客通知
🛠 技术工具
"""

    await update.message.reply_text(text)


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):

    result = update.chat_member

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    if old_status == "left" and new_status == "member":

        user = result.new_chat_member.user

        text = f"""
👋 欢迎 {user.first_name} 加入古道北技术交流群！

这里交流：

📚 Hugo博客
🤖 AI探索
💻 GitHub项目
🌐 网络技术

博客：
https://zidane.us.ci/

欢迎交流学习！
"""

        await context.bot.send_message(
            chat_id=result.chat.id,
            text=text
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📚 古道北助手帮助

/start 开始
/help 查看帮助
/blog 查看博客
/project 查看项目
/about 关于我
/github GitHub项目
/status 系统状态
/contact 联系方式
"""

    await update.message.reply_text(text)


async def blog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "古道北博客：\nhttps://zidane.us.ci/"
    )


async def project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "我的项目：\n\n🌿 古道景观设计\nhttps://landscape.zidane.us.ci/"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
👤 关于古道北

记录个人学习与折腾历程。

方向：

🌐 网络技术
💻 Linux / VPS
📝 Hugo博客
🤖 AI探索
🌿 项目设计

博客：
https://zidane.us.ci/

欢迎交流学习。
"""

    await update.message.reply_text(text)



async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
💻 GitHub

主页：
https://github.com/wumingdanwu-wq

我的项目：

📝 Gudaobei-Blog
博客系统

🌿 landscape-design
景观设计展示

🤖 GudaoBeiBot
Telegram机器人
"""

    await update.message.reply_text(text)



async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
📡 古道北助手状态

机器人：
✅ 运行中

博客：
✅ 在线

GitHub：
✅ 正常

当前版本：
v1.0
"""

    await update.message.reply_text(text)



async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
📮 联系方式

Telegram：
待添加

GitHub：
https://github.com/wumingdanwu-wq

博客：
https://zidane.us.ci/
"""

    await update.message.reply_text(text)
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("blog", blog))
    app.add_handler(CommandHandler("project", project))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("github", github))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("contact", contact))

    app.add_handler(
        ChatMemberHandler(
            welcome,
            ChatMemberHandler.CHAT_MEMBER
    )
)

    print("古道北助手启动成功")

    app.run_polling()


if __name__ == "__main__":
    main()