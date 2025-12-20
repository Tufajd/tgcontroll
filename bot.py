import asyncio
import subprocess
import logging
import socket
import os
import sys
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]
LOG_FILE = "logs/actions.log"

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

state = {}

def ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

def log(user, cmd, res):
    logging.info(f"user={user} | ip={ip()} | cmd={cmd} | result={res[:200]}")

async def run(cmd, timeout=5):
    try:
        p = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            o, e = await asyncio.wait_for(p.communicate(), timeout)
        except asyncio.TimeoutError:
            p.kill()
            return False, "timeout (killed)"
        out = o.decode().strip() or e.decode().strip()
        return True, out if out else "no output"
    except Exception as e:
        return False, str(e)

async def api_ok():
    ok, _ = await run("termux-info", timeout=2)
    return ok

keyboard = ReplyKeyboardMarkup(
    [
        ["🟢 Пинг", "🔋 Батарея"],
        ["📡 Сеть", "📍 Геолокация"],
        ["🔊 Громкость", "📋 Буфер"],
        ["📷 Камера", "📸 Скриншот"],
        ["📱 Устройство", "📳 Вибрация"],
        ["🔔 Уведомление"],
        ["🛰 Watchdog", "♻ Перезапуск"],
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    await update.message.reply_text(
        f"Бот успешно запущен и готов к работе\n\n"
        f"Дата: {now}\n"
        f"Пользователь: {update.effective_user.username}\n"
        f"ID пользователя: {update.effective_user.id}\n"
        f"ID чата: {update.effective_chat.id}",
        reply_markup=keyboard
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED_USERS:
        return

    text = update.message.text

    if uid in state and text.startswith(("🟢","🔋","📡","📍","🔊","📋","📷","📸","📱","📳","🔔","🛰","♻")):
        del state[uid]

    msg = await update.message.reply_text("⏳ Выполняется...")

    if text == "🟢 Пинг":
        out = "pong"

    elif text == "🔋 Батарея":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-battery-status")

    elif text == "📡 Сеть":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-wifi-connectioninfo")

    elif text == "📍 Геолокация":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-location")

    elif text == "🔊 Громкость":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-volume")

    elif text == "📋 Буфер":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-clipboard-get")

    elif text == "📷 Камера":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-camera-photo /sdcard/photo.jpg")
        out = "Saved /sdcard/photo.jpg"

    elif text == "📸 Скриншот":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        path = "/sdcard/screen.png"
        ok, _ = await run(f"termux-screenshot -f {path}")
        if ok and os.path.exists(path):
            await msg.delete()
            await update.message.reply_photo(open(path, "rb"))
            log(uid, text, "screenshot sent")
            return
        out = "screenshot failed"

    elif text == "📱 Устройство":
        _, out = await run("getprop ro.product.model")

    elif text == "📳 Вибрация":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-vibrate -d 500")
        out = "ok"

    elif text == "🔔 Уведомление":
        if not await api_ok():
            await msg.edit_text("❌ Termux API не отвечает")
            return
        _, out = await run("termux-notification -t Bot -c Running")
        out = "sent"

    elif text == "🛰 Watchdog":
        api = await api_ok()
        proc, _ = await run("ps | grep bot.py", timeout=2)
        out = f"API: {'OK' if api else 'FAIL'}\nBOT: {'OK' if proc else 'FAIL'}"

    elif text == "♻ Перезапуск":
        await msg.edit_text("♻ Перезапуск бота...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    else:
        out = "unknown command"

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
