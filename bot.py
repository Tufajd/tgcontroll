            import asyncio
import subprocess
import logging
import os
import sys
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]

BASE_DIR = "/storage/emulated/0/TG_MANAGER"
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/session.log"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

def log(msg):
    logging.info(msg)

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
            return False, "command returned empty output"
        return True, data
    except asyncio.TimeoutError:
        return False, "timeout"
    except Exception as e:
        return False, str(e)

async def progress(msg):
    for p in range(0, 96, 5):
        bar = "▰" * (p // 10) + "▱" * (10 - p // 10)
        try:
            await msg.edit_text(f"⏳ Выполняется...\n{bar} {p}%")
        except:
            pass
        await asyncio.sleep(0.25)

keyboard = ReplyKeyboardMarkup(
    [
        ["🟢 Пинг", "💻 Термукс"],
        ["📂 Файлы", "📸 Скриншот"],
        ["🔌 ADB", "🛰 Watchdog"],
        ["♻ Перезапуск"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    context.user_data["cwd"] = BASE_DIR
    context.user_data["mode"] = None

    await update.message.reply_text(
        f"Бот успешно запущен и готов к работе\n\n"
        f"Дата: {now}\n"
        f"Пользователь: {update.effective_user.username}\n"
        f"ID пользователя: {update.effective_user.id}\n"
        f"ID чата: {update.effective_chat.id}",
        reply_markup=keyboard
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    text = update.message.text
    cwd = context.user_data.get("cwd", BASE_DIR)
    mode = context.user_data.get("mode")

    msg = await update.message.reply_text("⏳ Выполняется...")
    asyncio.create_task(progress(msg))

    if text == "🟢 Пинг":
        await msg.edit_text("pong")
        return

    if text == "💻 Термукс":
        context.user_data["mode"] = "termux"
        await msg.edit_text("Введите команду Termux")
        return

    if mode == "termux":
        ok, out = await run(text)
        context.user_data["mode"] = None
        await msg.edit_text(out if ok else f"❌ {out}")
        return

    if text == "📂 Файлы":
        context.user_data["mode"] = "files"
        await msg.edit_text(f"📂 {cwd}\n\nls | cd путь | cd ..")
        return

    if mode == "files":
        if text.startswith("cd"):
            path = text.replace("cd", "").strip()
            if path == "..":
                cwd = os.path.dirname(cwd)
            else:
                new = os.path.join(cwd, path)
                if os.path.isdir(new):
                    cwd = new
                else:
                    await msg.edit_text("❌ Папка не найдена")
                    return
            context.user_data["cwd"] = cwd
            await msg.edit_text(f"📂 {cwd}")
            return

        ok, out = await run(f"cd '{cwd}' && {text}")
        await msg.edit_text(out if ok else f"❌ {out}")
        return

    if text == "📸 Скриншот":
        path = "/sdcard/screen.png"
        ok, out = await run(f"termux-screenshot -f {path}")
        if ok and os.path.exists(path):
            await msg.delete()
            await update.message.reply_photo(open(path, "rb"))
        else:
            await msg.edit_text("❌ Termux API не отвечает")
        return

    if text == "🔌 ADB":
        context.user_data["mode"] = "adb_ip"
        await msg.edit_text("Введите IP")
        return

    if mode == "adb_ip":
        context.user_data["adb_ip"] = text.strip()
        context.user_data["mode"] = "adb_port"
        await msg.edit_text("Введите PORT")
        return

    if mode == "adb_port":
        context.user_data["adb_port"] = text.strip()
        context.user_data["mode"] = "adb_code"
        await msg.edit_text("Введите CODE")
        return

    if mode == "adb_code":
        ip = context.user_data["adb_ip"]
        port = context.user_data["adb_port"]
        code = text.strip()
        context.user_data["mode"] = None
        ok, out = await run(f"adb pair {ip}:{port} {code}", timeout=15)
        await msg.edit_text(out if ok else f"❌ {out}")
        return

    if text == "🛰 Watchdog":
        ok, _ = await run("termux-info")
        await msg.edit_text("API OK" if ok else "API FAIL")
        return

    if text == "♻ Перезапуск":
        await msg.edit_text("♻ Перезапуск...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

def main():
    print("BOT ACTIVE")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    app.run_polling()

if __name__ == "__main__":
    main()
