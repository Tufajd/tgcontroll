import os
import subprocess
import logging
import socket
import asyncio
import time
import sys
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]

BASE_DIR = os.getcwd()
CWD = BASE_DIR
DOWNLOAD_DIR = "/storage/emulated/0/TG_Manager"
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/actions.log"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

ENV = os.environ.copy()
ENV["PATH"] = "/data/data/com.termux/files/usr/bin:" + ENV.get("PATH", "")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

print("🤖 BOT ACTIVE (TERMUX)")

def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

def log(user, cmd, result):
    logging.info(f"user={user} | ip={get_ip()} | cmd='{cmd}' | result='{result[:200]}'")

async def run(cmd, timeout=10, retries=2):
    for _ in range(retries):
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=CWD,
                env=ENV
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode().strip() or stderr.decode().strip()
            if out:
                return out
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            return str(e)
    return "watchdog: command failed"

async def watchdog_check():
    try:
        proc = await asyncio.create_subprocess_shell(
            "termux-battery-status",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=ENV
        )
        await asyncio.wait_for(proc.communicate(), timeout=5)
        return True
    except:
        return False

async def progress(msg, duration=4.0):
    start = time.time()
    while True:
        p = min(int(((time.time() - start) / duration) * 100), 99)
        bar = "▰" * (p // 10) + "▱" * (10 - p // 10)
        try:
            await msg.edit_text(f"⏳ Выполняется...\n{bar} {p}%")
        except:
            pass
        if p >= 99:
            break
        await asyncio.sleep(0.3)

KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🟢 Пинг", "🔋 Батарея"],
        ["📡 Сеть", "📍 Геолокация"],
        ["🔊 Громкость", "📋 Буфер"],
        ["📷 Камера", "📂 Файлы"],
        ["📱 Устройство", "📳 Вибрация"],
        ["🔔 Уведомление"],
        ["📁 Менеджер", "🖥 Термукс"],
        ["📡 Watchdog", "♻️ Перезапуск"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if u.id not in ALLOWED_USERS:
        return
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    text = (
        "Бот успешно запущен и готов к работе\n\n"
        f"Дата: {now}\n"
        f"Пользователь: {u.username}\n"
        f"ID пользователя: {u.id}\n"
        f"ID чата: {update.effective_chat.id}"
    )
    await update.message.reply_text(text, reply_markup=KEYBOARD)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CWD
    uid = update.effective_user.id
    if uid not in ALLOWED_USERS:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("⏳ Выполняется...\n▱▱▱▱▱▱▱▱▱▱ 0%")
    prog = asyncio.create_task(progress(msg))

    try:
        if text == "🟢 Пинг":
            out = "pong"

        elif text == "📡 Watchdog":
            ok = await watchdog_check()
            out = "termux api ok" if ok else "termux api not responding"

        elif text == "♻️ Перезапуск":
            log(uid, "restart", "manual")
            await msg.edit_text("♻️ Перезапуск бота...")
            os.execv(sys.executable, [sys.executable] + sys.argv)

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

        elif text == "📁 Менеджер":
            out = "ls | cd путь | cd .. | pwd | get файл | rm файл | mv a b | mkdir имя | touch имя | wget ссылка"

        elif text == "pwd":
            out = CWD

        elif text == "ls":
            out = "\n".join(os.listdir(CWD)) or "пусто"

        elif text.startswith("cd "):
            p = text[3:].strip()
            if p == "..":
                CWD = os.path.dirname(CWD)
                out = CWD
            else:
                np = os.path.abspath(os.path.join(CWD, p))
                if os.path.isdir(np):
                    CWD = np
                    out = CWD
                else:
                    out = "нет такой папки"

        elif text.startswith("wget "):
            out = await run(f"wget -P {DOWNLOAD_DIR} {text[5:].strip()}")

        elif text.startswith("get "):
            f = os.path.join(CWD, text[4:].strip())
            await update.message.reply_document(InputFile(f))
            out = "sent"

        else:
            out = await run(text)

        log(uid, text, out)

    except Exception as e:
        out = f"error: {e}"
        log(uid, text, out)

    prog.cancel()
    await msg.edit_text(out[:4000] or "ok")

while True:
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
        app.run_polling()
    except Exception as e:
        logging.info(f"watchdog restart: {e}")
        time.sleep(3)
