import os
import json
import logging
import yt_dlp
import requests
import asyncio
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import Router

# Telegram bot tokeni
TOKEN = "8052311671:AAHLe7lgPnS848v8IqBQxscAHNOeq2pQeE4"
BOT_USERNAME = "karimovsavebot"
ADMIN_ID = 1483283523

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
logging.basicConfig(level=logging.INFO)

USERS_FILE = "users.json"
REQUESTS_FILE = "requests.json"


# Foydalanuvchilarni yuklash

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}


# Foydalanuvchilarni saqlash
def save_user(user_id):
    users = load_users()
    users[str(user_id)] = datetime.now().isoformat()
    with open(USERS_FILE, "w") as file:
        json.dump(users, file)


# Oxirgi 24 soat, 7 kun va 30 kun ichida qo‘shilgan foydalanuvchilar
def get_recent_users(days):
    users = load_users()
    threshold = datetime.now() - timedelta(days=days)
    return sum(1 for date in users.values() if isinstance(date, str) and datetime.fromisoformat(date) > threshold)


def get_total_users():
    return len(load_users())


# So‘rovlarni saqlash
def save_request():
    now = datetime.now().isoformat()
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as file:
            requests_list = json.load(file)
    else:
        requests_list = []
    requests_list.append(now)
    with open(REQUESTS_FILE, "w") as file:
        json.dump(requests_list, file)


# Oxirgi 24 soat, 7 kun va 30 kun ichidagi so‘rovlar
def get_recent_requests(days):
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as file:
            requests_list = json.load(file)
    else:
        return 0
    threshold = datetime.now() - timedelta(days=days)
    return sum(1 for date in requests_list if isinstance(date, str) and datetime.fromisoformat(date) > threshold)


def download_video(url):
    options = {
        'format': 'best',
        'quiet': True,
        'outtmpl': 'downloads/video.%(ext)s'
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
        except Exception as e:
            logging.error(f"Video yuklab olishda xatolik: {e}")
            return None


def get_group_invite_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Guruhga qo‘shish", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]]
    )


@router.message(Command("start"))
async def start_command(message: Message):
    save_user(message.from_user.id)
    await message.answer("👋 Salom! Instagram yoki TikTok video/rasm yuklash uchun havolani yuboring.")


@router.message(Command("stats"))
async def stats_command(message: Message):
    if message.from_user.id == ADMIN_ID:
        total_users = get_total_users()
        new_users_24h = get_recent_users(1)
        new_users_7d = get_recent_users(7)
        new_users_30d = get_recent_users(30)

        requests_24h = get_recent_requests(1)
        requests_7d = get_recent_requests(7)
        requests_30d = get_recent_requests(30)

        stats_text = f"""
📊 **Statistika**

👥 **Foydalanuvchilar**:
├ Jami: {total_users}
├ Oxirgi 24 soat: {new_users_24h}
├ Oxirgi 7 kun: {new_users_7d}
└ Oxirgi 30 kun: {new_users_30d}

🔀 **So‘rovlar**:
├ Oxirgi 24 soat: {requests_24h}
├ Oxirgi 7 kun: {requests_7d}
└ Oxirgi 30 kun: {requests_30d}
        """
        await message.answer(stats_text)
    else:
        await message.answer("❌ Sizda bu buyruqdan foydalanish huquqi yo‘q.")


@router.message(F.text.contains("instagram.com") | F.text.contains("tiktok.com"))
async def handle_media(message: Message):
    save_user(message.from_user.id)
    save_request()
    await message.answer("📥 Yuklab olayapman, biroz kuting...")
    try:
        file_path = download_video(message.text)
        if file_path and os.path.exists(file_path):
            await bot.send_video(message.chat.id, FSInputFile(file_path),
                                 caption=f"📥 @{BOT_USERNAME} orqali yuklab olindi")
            os.remove(file_path)
        else:
            await message.answer("❌ Video yuklab bo‘lmadi.")
    except Exception as e:
        logging.error(f"Video yuklab olishda xatolik: {e}")
        await message.answer("❌ Yuklab olishda xatolik yuz berdi.")


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
