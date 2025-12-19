import os
import subprocess
import logging
import socket
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
CHAT_ID = 6504292955
ALLOWED_USERS = [6504292955]

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "actions.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"

def log_action(user, command, result):
    ip = get_local_ip()
    logging.info(
        f"user_id={user.id} | username={user.username} | ip={ip} | cmd='{command}' | result='{result}'"
    )

def allowed(update: Update):
    return update.effective_user and update.effective_user.id in ALLOWED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    await update.message.reply_text("🤖 Бот готов к работе")

async def shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    if not context.args:
        await update.message.reply_text("❌ Нет команды")
        return

    cmd = " ".join(context.args)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=8
        )
        output = (result.stdout or result.stderr).strip()
        output_short = output[:3500] if output else "OK"

        await update.message.reply_text(
            f"💻 Результат:\n```\n{output_short}\n```",
            parse_mode="Markdown"
        )

        log_action(update.effective_user, cmd, "success")

    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ Таймаут")
        log_action(update.effective_user, cmd, "timeout")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        log_action(update.effective_user, cmd, f"error:{e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return

    text = update.message.text.strip()

    if text.lower().startswith("shell "):
        context.args = [text[6:]]
        await shell_command(update, context)
    else:
        await update.message.reply_text("❌ Неизвестная команда")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()