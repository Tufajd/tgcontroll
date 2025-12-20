import asyncio
import subprocess
import logging
import socket
import time
import os
import sys
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]
LOG_FILE = "logs/actions.log"

os.makedirs("logs", exist_ok=True)
BASE_DIR = "/storage/emulated/0/tg_manager"
os.makedirs(BASE_DIR, exist_ok=True)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s | %(message)s")

state = {}
cwd = BASE_DIR
stream_task = None

def ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

def log(user, cmd, res):
    logging.info(f"user={user} | ip={ip()} | cmd={cmd} | result={res[:200]}")

async def run(cmd, timeout=10):
    try:
        p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        o, e = await asyncio.wait_for(p.communicate(), timeout)
        d = o.decode().strip() or e.decode().strip()
        return bool(d), d if d else "command failed"
    except asyncio.TimeoutError:
        return False, "timeout"
    except Exception as e:
        return False, str(e)

async def progress(msg):
    for i in range(0, 100, 5):
        bar = "▰" * (i // 10) + "▱" * (10 - i // 10)
        try:
            await msg.edit_text(f"⏳ Выполняется...\n{bar} {i}%")
        except:
            pass
        await asyncio.sleep(0.3)

keyboard = ReplyKeyboardMarkup(
    [
        ["🟢 Пинг", "🔋 Батарея"],
        ["📡 Сеть", "📍 Геолокация"],
        ["🔊 Громкость", "📋 Буфер"],
        ["📷 Камера", "📸 Скриншот"],
        ["📱 Устройство", "📳 Вибрация"],
        ["📂 Файлы", "💻 Термукс"],
        ["📺 Стрим", "🛰 Watchdog"],
        ["🔌 ADB", "♻ Перезапуск"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    await update.message.reply_text(
        f"Бот успешно запущен и готов к работе\n\nДата: {now}\nПользователь: {update.effective_user.username}\nID пользователя: {update.effective_user.id}\nID чата: {update.effective_chat.id}",
        reply_markup=keyboard
    )

async def stream_loop(chat):
    while True:
        path = "/sdcard/stream.png"
        await run(f"termux-screenshot -f {path}")
        if os.path.exists(path):
            await chat.send_photo(open(path, "rb"))
        await asyncio.sleep(2)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cwd, stream_task
    uid = update.effective_user.id
    if uid not in ALLOWED_USERS:
        return

    text = update.message.text

    if uid in state:
        s = state[uid]
        if s["mode"] == "adb_ip":
            s["ip"] = text
            s["mode"] = "adb_port"
            await update.message.reply_text("Введите PORT")
            return
        if s["mode"] == "adb_port":
            s["port"] = text
            s["mode"] = "adb_code"
            await update.message.reply_text("Введите CODE")
            return
        if s["mode"] == "adb_code":
            cmd = f"adb pair {s['ip']}:{s['port']} {text} && adb connect {s['ip']}:{s['port']}"
            ok, out = await run(cmd)
            del state[uid]
            await update.message.reply_text(out)
            return

    msg = await update.message.reply_text("⏳ Выполняется...")
    asyncio.create_task(progress(msg))

    if text == "🟢 Пинг":
        out = "pong"

    elif text == "🔋 Батарея":
        _, out = await run("termux-battery-status")

    elif text == "📡 Сеть":
        _, out = await run("termux-wifi-connectioninfo")

    elif text == "📍 Геолокация":
        _, out = await run("termux-location")

    elif text == "🔊 Громкость":
        _, out = await run("termux-volume")

    elif text == "📋 Буфер":
        _, out = await run("termux-clipboard-get")

    elif text == "📷 Камера":
        await run("termux-camera-photo /sdcard/photo.jpg")
        out = "saved /sdcard/photo.jpg"

    elif text == "📸 Скриншот":
        path = "/sdcard/screen.png"
        await run(f"termux-screenshot -f {path}")
        await msg.delete()
        await update.message.reply_photo(open(path, "rb"))
        return

    elif text == "📱 Устройство":
        _, out = await run("getprop ro.product.model")

    elif text == "📳 Вибрация":
        await run("termux-vibrate -d 500")
        out = "ok"

    elif text == "📂 Файлы":
        out = f"Текущая папка:\n{cwd}\n\nls\ncd <path>\nrm <file>\nmkdir <dir>\nwget <url>"

    elif text.startswith("cd "):
        p = os.path.abspath(os.path.join(cwd, text[3:]))
        if os.path.isdir(p):
            cwd = p
            out = cwd
        else:
            out = "no such dir"

    elif text.startswith("ls"):
        out = "\n".join(os.listdir(cwd))[:4000]

    elif text.startswith("rm "):
        os.remove(os.path.join(cwd, text[3:]))
        out = "deleted"

    elif text.startswith("mkdir "):
        os.makedirs(os.path.join(cwd, text[6:]), exist_ok=True)
        out = "created"

    elif text.startswith("wget "):
        _, out = await run(f"wget {text[5:]} -P {BASE_DIR}")

    elif text == "💻 Термукс":
        out = "Введите команду"

    elif text.startswith("$"):
        _, out = await run(text[1:])

    elif text == "📺 Стрим":
        if not stream_task:
            stream_task = asyncio.create_task(stream_loop(update.effective_chat))
            out = "stream started"
        else:
            stream_task.cancel()
            stream_task = None
            out = "stream stopped"

    elif text == "🛰 Watchdog":
        _, out = await run("termux-info")

    elif text == "🔌 ADB":
        state[uid] = {"mode": "adb_ip"}
        await msg.edit_text("Введите IP адрес")
        return

    elif text == "♻ Перезапуск":
        await msg.edit_text("Перезапуск...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    else:
        out = "unknown"

    log(uid, text, out)
    await msg.edit_text(out[:4000])

def main():
    print("BOT ACTIVE")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    app.run_polling()

if __name__ == "__main__":
    main()
