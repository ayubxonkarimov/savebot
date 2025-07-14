import os
import json
import logging
import yt_dlp
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import Command
from aiogram import Router

# 🔐 Tokenlar
BOT1_TOKEN = "8052311671:AAGP3FGTjhBAveq__iOCgme3N7--Pmnyvu0"  # musiqa bot
BOT2_TOKEN = "7513721714:AAGf_y_Z76kGE5slc4u8NqYQLOtbEEcGg9U"  # admin bot
ADMIN_ID = 1483283523

# 📦 Fayllar
USERS_FILE = "users.json"
REQUESTS_FILE = "requests.json"

# 🧠 Botlar va routerlar
bot1 = Bot(token=BOT1_TOKEN)
bot2 = Bot(token=BOT2_TOKEN)
dp1 = Dispatcher()
dp2 = Dispatcher()
router1 = Router()
router2 = Router()
logging.basicConfig(level=logging.INFO)

# 📥 Broadcast holati
broadcast_state = {}

# 📁 JSON funksiyalar
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_user(user_id):
    users = load_users()
    users[str(user_id)] = datetime.now().isoformat()
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

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

def get_recent_users(days):
    users = load_users()
    threshold = datetime.now() - timedelta(days=days)
    return sum(1 for d in users.values() if isinstance(d, str) and datetime.fromisoformat(d) > threshold)

def get_recent_requests(days):
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as file:
            requests_list = json.load(file)
    else:
        return 0
    threshold = datetime.now() - timedelta(days=days)
    return sum(1 for d in requests_list if isinstance(d, str) and datetime.fromisoformat(d) > threshold)

def get_total_users():
    return len(load_users())

# 📥 Video yuklash
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
            logging.error(f"Video yuklash xatosi: {e}")
            return None

# 🎛️ Menyu
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Habar yuborish")]
        ],
        resize_keyboard=True
    )

# =================== 1-BOT ===================

@router1.message(Command("start"))
async def bot1_start(message: Message):
    save_user(message.from_user.id)
    await message.answer("👋 Instagram yoki TikTok havolasini yuboring.")


@router1.message(F.text.contains("instagram.com") | F.text.contains("tiktok.com"))
async def handle_video(message: Message):
    save_user(message.from_user.id)
    save_request()
    await message.answer("📥 Yuklab olayapman...")

    try:
        file_path = download_video(message.text)
        if file_path and os.path.exists(file_path):
            await bot1.send_video(message.chat.id, FSInputFile(file_path),
                                  caption="📥 Yuklab olindi.")
            os.remove(file_path)
        else:
            await message.answer("❌ Yuklab bo‘lmadi.")
    except Exception as e:
        logging.error(str(e))
        await message.answer("❌ Xatolik yuz berdi.")


@router1.message(F.text.regexp(r"^[\w\s’'-]+[-–][\w\s’'-]+$"))
async def music_buttons(message: Message):
    text = message.text
    parts = [p.strip() for p in text.replace("–", "-").split("-")]
    if len(parts) != 2:
        await message.answer("Format: Qo‘shiq – Ijrochi")
        return

    song, artist = parts
    q = f"{song} {artist}".replace(" ", "+")
    artist_q = artist.replace(" ", "+")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Google", url=f"https://www.google.com/search?q={q}")],
        [InlineKeyboardButton("YouTube", url=f"https://www.youtube.com/results?search_query={q}")],
        [InlineKeyboardButton("YouTube Music", url=f"https://music.youtube.com/search?q={q}")],
        [InlineKeyboardButton("Spotify", url=f"https://open.spotify.com/search/{q}")],
        [InlineKeyboardButton("Apple Music", url=f"https://music.apple.com/us/search?term={q}")],
        [InlineKeyboardButton("🎨 Rassom bo‘yicha qidirish", url=f"https://www.google.com/search?q={artist_q}")]
    ])
    await message.answer(f"🎵 {song} – {artist} bo‘yicha qidiruv:", reply_markup=keyboard)

# =================== 2-BOT (Admin) ===================

@router2.message(Command("start"))
async def bot2_start(message: Message):
    await message.answer("📋 Admin panelga xush kelibsiz", reply_markup=get_main_menu())


@router2.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz.")

    users = get_total_users()
    users_24h = get_recent_users(1)
    users_7d = get_recent_users(7)
    users_30d = get_recent_users(30)

    req_24h = get_recent_requests(1)
    req_7d = get_recent_requests(7)
    req_30d = get_recent_requests(30)

    text = f"""
📊 <b>Statistika</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {users}
├ 24 soat: {users_24h}
├ 7 kun: {users_7d}
└ 30 kun: {users_30d}

📥 <b>So‘rovlar:</b>
├ 24 soat: {req_24h}
├ 7 kun: {req_7d}
└ 30 kun: {req_30d}
    """
    await message.answer(text, parse_mode="HTML")


@router2.message(F.text == "📢 Habar yuborish")
async def ask_broadcast_text(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Sizga ruxsat yo‘q.")
    broadcast_state[message.from_user.id] = True
    await message.answer("✍️ Yubormoqchi bo‘lgan xabaringizni yozing:")


@router2.message()
@router2.message()
async def handle_broadcast_input(message: Message):
    if broadcast_state.get(message.from_user.id):
        broadcast_state[message.from_user.id] = False
        users = load_users()
        ok = fail = 0

        for uid in users:
            try:
                # 🧠 Matnli xabar bo‘lsa
                if message.text:
                    await bot1.send_message(uid, message.text)
                # 🖼️ Rasm bo‘lsa
                elif message.photo:
                    photo = message.photo[-1].file_id
                    await bot1.send_photo(uid, photo, caption=message.caption or "")
                # 📹 Video bo‘lsa
                elif message.video:
                    await bot1.send_video(uid, message.video.file_id, caption=message.caption or "")
                # 📦 Fayl bo‘lsa
                elif message.document:
                    await bot1.send_document(uid, message.document.file_id, caption=message.caption or "")
                # 😺 Stiker bo‘lsa
                elif message.sticker:
                    await bot1.send_sticker(uid, message.sticker.file_id)
                else:
                    fail += 1
                    continue

                ok += 1
            except Exception as e:
                logging.warning(f"❌ {uid} ga yuborilmadi: {e}")
                fail += 1

        await message.answer(f"📢 Yuborildi: {ok} ta\n❌ Xatolik: {fail} ta")

# =================== RUN ===================

async def main():
    dp1.include_router(router1)
    dp2.include_router(router2)
    await asyncio.gather(
        dp1.start_polling(bot1),
        dp2.start_polling(bot2)
    )

if __name__ == "__main__":
    asyncio.run(main())
