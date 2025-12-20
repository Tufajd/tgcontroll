import os
import subprocess
import logging
import socket
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "actions.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "unknown"

def log(user, cmd, result):
    logging.info(
        f"user={user.id} | ip={get_ip()} | cmd='{cmd}' | result='{result}'"
    )

def allowed(update: Update):
    return update.effective_user and update.effective_user.id in ALLOWED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    await update.message.reply_text(
        "🤖 Termux Controller Bot\n\n"
        "Команды:\n"
        "скриншот\n"
        "батарея\n"
        "память\n"
        "shell <команда>\n"
        "файл <путь>\n"
        "лог"
    )

async def screenshot(update: Update):
    path = "/sdcard/screen.png"
    try:
        subprocess.run(
            ["termux-screenshot", "-f", path],
            check=True
        )
        with open(path, "rb") as f:
            await update.message.reply_photo(f)
        log(update.effective_user, "screenshot", "ok")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        log(update.effective_user, "screenshot", "error")

async def battery(update: Update):
    try:
        r = subprocess.run(
            ["termux-battery-status"],
            capture_output=True,
            text=True
        )
        await update.message.reply_text(r.stdout)
        log(update.effective_user, "battery", "ok")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        log(update.effective_user, "battery", "error")

async def memory(update: Update):
    try:
        r = subprocess.run(
            ["free", "-h"],
            capture_output=True,
            text=True
        )
        await update.message.reply_text(f"```\n{r.stdout}\n```", parse_mode="Markdown")
        log(update.effective_user, "memory", "ok")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        log(update.effective_user, "memory", "error")

async def shell(update: Update, cmd: str):
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=8
        )
        out = (r.stdout or r.stderr).strip()[:3500]
        await update.message.reply_text(
            f"```\n{out if out else 'OK'}\n```",
            parse_mode="Markdown"
        )
        log(update.effective_user, cmd, "ok")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ Таймаут")
        log(update.effective_user, cmd, "timeout")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        log(update.effective_user, cmd, "error")

async def send_log(update: Update):
    try:
        with open(LOG_FILE, "rb") as f:
            await update.message.reply_document(f)
    except:
        await update.message.reply_text("❌ Лог пуст или недоступен")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return

    text = update.message.text.strip()

    if text == "скриншот":
        await screenshot(update)

    elif text == "батарея":
        await battery(update)

    elif text == "память":
        await memory(update)

    elif text.startswith("shell "):
        await shell(update, text[6:])

    elif text.startswith("файл "):
        path = text[5:]
        try:
            with open(path, "rb") as f:
                await update.message.reply_document(f)
        except:
            await update.message.reply_text("❌ Файл не найден")

    elif text == "лог":
        await send_log(update)

    else:
        await update.message.reply_text("❌ Неизвестная команда")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("🤖 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
