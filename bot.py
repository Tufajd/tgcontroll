import os
import subprocess
import logging
import datetime
import socket
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]

LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/actions.log"

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

def log(action, user):
    ip = socket.gethostbyname(socket.gethostname())
    logging.info(f"user={user} ip={ip} action={action}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return
    await update.message.reply_text(
        "📱 Termux Controller Bot\n\n"
        "Команды:\n"
        "скриншот\n"
        "батарея\n"
        "память\n"
        "shell <команда>\n"
        "лог"
    )

async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    log("battery", user)
    try:
        r = subprocess.run(
            ["termux-battery-status"],
            capture_output=True,
            text=True
        )
        await update.message.reply_text(r.stdout)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    log("memory", user)
    r = subprocess.run(["free", "-h"], capture_output=True, text=True)
    await update.message.reply_text(f"```\n{r.stdout}\n```", parse_mode="Markdown")

async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if not context.args:
        await update.message.reply_text("shell <команда>")
        return
    cmd = " ".join(context.args)
    log(f"shell: {cmd}", user)
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        out = r.stdout or r.stderr or "пусто"
        await update.message.reply_text(f"```\n{out[:4000]}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def show_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("Лог пуст")
        return
    with open(LOG_FILE, "r") as f:
        data = f.read()[-4000:]
    await update.message.reply_text(f"```\n{data}\n```", parse_mode="Markdown")

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    text = update.message.text.strip().lower()

    elif text == "батарея":
        await battery(update, context)
    elif text == "память":
        await memory(update, context)
    elif text.startswith("shell "):
        context.args = text.split()[1:]
        await shell(update, context)
    elif text == "лог":
        await show_log(update, context)
    else:
        await update.message.reply_text("Неизвестная команда")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("🤖 Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
