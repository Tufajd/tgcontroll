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
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

def log(user, cmd, result):
    logging.info(f"user={user} | ip={get_ip()} | cmd={cmd} | result={result[:200]}")

def cmd_exists(cmd):
    return subprocess.call(
        f"command -v {cmd}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0

async def run(cmd, timeout=8):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
        data = out.decode().strip() or err.decode().strip()
        if not data:
            return False, "команда выполнилась, но вернула пустой результат"
        return True, data
    except asyncio.TimeoutError:
        return False, "таймаут выполнения команды"
    except Exception as e:
        return False, str(e)

async def progress(msg, duration=4):
    start = time.time()
    while True:
        percent = min(int(((time.time() - start) / duration) * 100), 99)
        bar = "▰" * (percent // 10) + "▱" * (10 - percent // 10)
        try:
            await msg.edit_text(f"⏳ Выполняется...\n{bar} {percent}%")
        except:
            pass
        if percent >= 99:
            break
        await asyncio.sleep(0.3)

keyboard = ReplyKeyboardMarkup(
    [
        ["🟢 Пинг", "🔋 Батарея"],
        ["📡 Сеть", "📍 Геолокация"],
        ["🔊 Громкость", "📋 Буфер"],
        ["📷 Камера", "📸 Скриншот"],
        ["📱 Устройство", "📳 Вибрация"],
        ["🔔 Уведомление"],
        ["🛰 Watchdog", "♻ Перезапуск"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    api_ok = cmd_exists("termux-battery-status")
    api_status = "OK" if api_ok else "НЕ НАЙДЕН"

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    await update.message.reply_text(
        f"Бот успешно запущен и готов к работе\n\n"
        f"Дата: {now}\n"
        f"Пользователь: {update.effective_user.username}\n"
        f"ID пользователя: {update.effective_user.id}\n"
        f"ID чата: {update.effective_chat.id}\n\n"
        f"Termux API: {api_status}",
        reply_markup=keyboard
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    text = update.message.text
    uid = update.effective_user.id

    msg = await update.message.reply_text("⏳ Выполняется...\n▱▱▱▱▱▱▱▱▱▱ 0%")
    prog = asyncio.create_task(progress(msg))

    ok = True
    out = ""

    def api_guard(cmd):
        if not cmd_exists(cmd):
            return False, f"❌ {cmd} недоступна\n\nПроверь:\n• установлен Termux:API\n• выданы разрешения\n• приложение Termux:API запущено"
        return True, ""

    if text == "🟢 Пинг":
        out = "pong"

    elif text == "🔋 Батарея":
        ok, err = api_guard("termux-battery-status")
        if ok:
            ok, out = await run("termux-battery-status")
        else:
            out = err

    elif text == "📡 Сеть":
        ok, err = api_guard("termux-wifi-connectioninfo")
        if ok:
            ok, out = await run("termux-wifi-connectioninfo")
        else:
            out = err

    elif text == "📍 Геолокация":
        ok, err = api_guard("termux-location")
        if ok:
            ok, out = await run("termux-location")
        else:
            out = err

    elif text == "🔊 Громкость":
        ok, err = api_guard("termux-volume")
        if ok:
            ok, out = await run("termux-volume")
        else:
            out = err

    elif text == "📋 Буфер":
        ok, err = api_guard("termux-clipboard-get")
        if ok:
            ok, out = await run("termux-clipboard-get")
        else:
            out = err

    elif text == "📷 Камера":
        ok, err = api_guard("termux-camera-photo")
        if not ok:
            out = err
        else:
            path = "/sdcard/photo.jpg"
            ok, out = await run(f"termux-camera-photo {path}")
            if ok and os.path.exists(path):
                await msg.delete()
                await update.message.reply_photo(open(path, "rb"))
                log(uid, text, "photo sent")
                return

    elif text == "📸 Скриншот":
        ok, err = api_guard("termux-screenshot")
        if not ok:
            out = err
        else:
            path = "/sdcard/screen.png"
            ok, out = await run(f"termux-screenshot -f {path}")
            if ok and os.path.exists(path):
                await msg.delete()
                await update.message.reply_photo(open(path, "rb"))
                log(uid, text, "screenshot sent")
                return

    elif text == "📱 Устройство":
        ok, out = await run("getprop ro.product.model")

    elif text == "📳 Вибрация":
        ok, err = api_guard("termux-vibrate")
        if ok:
            ok, out = await run("termux-vibrate -d 500")
            if ok:
                out = "вибрация выполнена"
        else:
            out = err

    elif text == "🔔 Уведомление":
        ok, err = api_guard("termux-notification")
        if ok:
            ok, out = await run("termux-notification -t Bot -c Running")
            if ok:
                out = "уведомление отправлено"
        else:
            out = err

    elif text == "🛰 Watchdog":
        if cmd_exists("termux-battery-status"):
            out = "watchdog: Termux API доступен"
        else:
            out = "watchdog: Termux API НЕ НАЙДЕН\nОткрой приложение Termux:API"

    elif text == "♻ Перезапуск":
        await msg.edit_text("♻ Перезапуск бота...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    else:
        out = "неизвестная команда"

    prog.cancel()
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
