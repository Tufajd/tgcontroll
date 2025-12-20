import subprocess
import logging
import socket
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]
LOG_FILE = "logs/actions.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

def run(cmd):
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return str(e)

def log(user, cmd, result):
    logging.info(
        f"user={user} | ip={get_ip()} | cmd='{cmd}' | result='{result[:200]}'"
    )

keyboard = ReplyKeyboardMarkup(
    [
        ["🔋 Батарея", "📡 Сеть"],
        ["📍 Геолокация", "🔊 Громкость"],
        ["📋 Буфер", "📷 Камера"],
        ["📂 Файлы", "📱 Устройство"],
        ["📳 Вибрация", "🔔 Уведомление"],
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return
    await update.message.reply_text(
        "🤖 Termux Control Bot",
        reply_markup=keyboard
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    text = update.message.text
    uid = update.effective_user.id

    if text == "🔋 Батарея":
        out = run("termux-battery-status")
    elif text == "📡 Сеть":
        out = run("termux-wifi-connectioninfo")
    elif text == "📍 Геолокация":
        out = run("termux-location")
    elif text == "🔊 Громкость":
        out = run("termux-volume")
    elif text == "📋 Буфер":
        out = run("termux-clipboard-get")
    elif text == "📷 Камера":
        run("termux-camera-photo /sdcard/photo.jpg")
        out = "saved /sdcard/photo.jpg"
    elif text == "📂 Файлы":
        out = run("ls /sdcard | head")
    elif text == "📱 Устройство":
        out = run("getprop ro.product.model")
    elif text == "📳 Вибрация":
        out = run("termux-vibrate -d 500")
    elif text == "🔔 Уведомление":
        out = run("termux-notification -t Bot -c Running")
    else:
        out = "unknown command"

    log(uid, text, out)
    await update.message.reply_text(out[:4000])

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
