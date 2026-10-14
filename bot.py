from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# 这里填写你的机器人 Token
import os

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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📚 古道北助手帮助

/start 开始
/help 帮助

/blog 博客地址
/project 项目展示
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


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("blog", blog))
    app.add_handler(CommandHandler("project", project))

    print("古道北助手启动成功")

    app.run_polling()


if __name__ == "__main__":
    main()