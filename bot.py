import os
import subprocess
import logging
import socket
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7566074976:AAE-Oj3Vo7BRz6eMG8S2nyjta05S-ZpmqGA"
ALLOWED_USERS = [6504292955]

BASE_DIR = os.getcwd()
DOWNLOAD_DIR = "/storage/emulated/0/TG_Manager"
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/session.log"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

CWD = BASE_DIR

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

def log(user, cmd, result):
    logging.info(f"user={user} | cmd='{cmd}' | result='{result}'")

def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

MAIN_KB = ReplyKeyboardMarkup(
    [["📁 Менеджер", "📡 Пинг"], ["📊 Выполняется"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    text = (
        "Бот успешно запущен и готов к работе\n\n"
        f"Дата: {now}\n"
        f"Пользователь: {u.username}\n"
        f"ID пользователя: {u.id}\n"
        f"ID чата: {c.id}"
    )
    await update.message.reply_text(text, reply_markup=MAIN_KB)

async def manager_info(update: Update):
    text = (
        "📁 Менеджер\n\n"
        "ls (показать файлы)\n"
        "пример: ls\n\n"
        "cd путь (перейти в папку)\n"
        "пример: cd Download\n\n"
        "cd .. (на уровень выше)\n\n"
        "pwd (текущий путь)\n\n"
        "get файл (отправить файл)\n"
        "пример: get test.txt\n\n"
        "rm файл (удалить)\n"
        "пример: rm old.txt\n\n"
        "mv старое новое (переименовать)\n"
        "пример: mv a.txt b.txt\n\n"
        "mkdir имя (создать папку)\n"
        "пример: mkdir test\n\n"
        "touch имя (создать файл)\n"
        "пример: touch a.txt\n\n"
        "wget ссылка (скачать файл)\n"
        f"Все загрузки → {DOWNLOAD_DIR}"
    )
    await update.message.reply_text(text)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CWD
    user = update.effective_user.id
    if user not in ALLOWED_USERS:
        return

    text = update.message.text.strip()

    if text == "📁 Менеджер":
        await manager_info(update)
        return

    if text == "📡 Пинг":
        await update.message.reply_text("pong")
        return

    if text == "📊 Выполняется":
        await update.message.reply_text("бот активен")
        return

    try:
        if text == "pwd":
            await update.message.reply_text(CWD)
            log(user, text, "ok")
            return

        if text == "ls":
            out = "\n".join(os.listdir(CWD))
            await update.message.reply_text(out or "пусто")
            log(user, text, "ok")
            return

        if text.startswith("cd "):
            path = text[3:].strip()
            if path == "..":
                CWD = os.path.dirname(CWD)
            else:
                new = os.path.abspath(os.path.join(CWD, path))
                if not os.path.isdir(new):
                    await update.message.reply_text("нет такой папки")
                    log(user, text, "fail")
                    return
                CWD = new
            await update.message.reply_text(CWD)
            log(user, text, "ok")
            return

        if text.startswith("mkdir "):
            os.mkdir(os.path.join(CWD, text[6:].strip()))
            await update.message.reply_text("создано")
            log(user, text, "ok")
            return

        if text.startswith("touch "):
            open(os.path.join(CWD, text[6:].strip()), "a").close()
            await update.message.reply_text("создано")
            log(user, text, "ok")
            return

        if text.startswith("rm "):
            os.remove(os.path.join(CWD, text[3:].strip()))
            await update.message.reply_text("удалено")
            log(user, text, "ok")
            return

        if text.startswith("mv "):
            _, a, b = text.split(maxsplit=2)
            os.rename(os.path.join(CWD, a), os.path.join(CWD, b))
            await update.message.reply_text("готово")
            log(user, text, "ok")
            return

        if text.startswith("get "):
            path = os.path.join(CWD, text[4:].strip())
            await update.message.reply_document(InputFile(path))
            log(user, text, "ok")
            return

        if text.startswith("wget "):
            url = text[5:].strip()
            subprocess.run(
                ["wget", "-P", DOWNLOAD_DIR, url],
                timeout=20
            )
            await update.message.reply_text(f"скачано в {DOWNLOAD_DIR}")
            log(user, text, "ok")
            return

        await update.message.reply_text("неизвестная команда")
        log(user, text, "unknown")

    except Exception as e:
        await update.message.reply_text(f"ошибка: {e}")
        log(user, text, "error")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
