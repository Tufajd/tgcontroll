import subprocess
import logging
import socket
import asyncio
import time
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

def log(user, cmd, result):
    logging.info(f"user={user} | ip={get_ip()} | cmd='{cmd}' | result='{result[:200]}'")

async def run(cmd, timeout=8):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode().strip() or stderr.decode().strip()
    except asyncio.TimeoutError:
        return "timeout"
    except Exception as e:
        return str(e)

async def progress_percent(msg, duration=4.0):
    start = time.time()
    while True:
        elapsed = time.time() - start
        p = min(int((elapsed / duration) * 100), 99)
        bars = int(p / 10)
        bar = "▰" * bars + "▱" * (10 - bars)
        try:
            await msg.edit_text(f"⏳ Выполняется...\n{bar} {p}%")
        except:
            pass
        if p >= 99:
            break
        await asyncio.sleep(0.3)

keyboard = ReplyKeyboardMarkup(
    [
        ["🟢 Пинг", "🔋 Батарея"],
        ["📡 Сеть", "📍 Геолокация"],
        ["🔊 Громкость", "📋 Буфер"],
        ["📷 Камера", "📂 Файлы"],
        ["📱 Устройство", "📳 Вибрация"],
        ["🔔 Уведомление"],
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return
    await update.message.reply_text("🤖 Termux Control Bot", reply_markup=keyboard)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    text = update.message.text
    uid = update.effective_user.id

    msg = await update.message.reply_text("⏳ Выполняется...\n▱▱▱▱▱▱▱▱▱▱ 0%")
    prog = asyncio.create_task(progress_percent(msg))

    if text == "🟢 Пинг":
        out = "pong"
    elif text == "🔋 Батарея":
        out = await run("termux-battery-status")
    elif text == "📡 Сеть":
        out = await run("termux-wifi-connectioninfo")
    elif text == "📍 Геолокация":
        out = await run("termux-location")
    elif text == "🔊 Громкость":
        out = await run("termux-volume")
    elif text == "📋 Буфер":
        out = await run("termux-clipboard-get")
    elif text == "📷 Камера":
        await run("termux-camera-photo /sdcard/photo.jpg")
        out = "saved /sdcard/photo.jpg"
    elif text == "📂 Файлы":
        out = await run("ls /sdcard | head")
    elif text == "📱 Устройство":
        out = await run("getprop ro.product.model")
    elif text == "📳 Вибрация":
        await run("termux-vibrate -d 500")
        out = "ok"
    elif text == "🔔 Уведомление":
        await run("termux-notification -t Bot -c Running")
        out = "sent"
    else:
        out = "unknown command"

    prog.cancel()
    log(uid, text, out)
    await msg.edit_text(out[:4000])

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("Бот активирован🫩")
    app.run_polling()

if __name__ == "__main__":
    main()
