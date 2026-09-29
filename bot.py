import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import logging
import re
import uuid
from typing import Dict
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramEntityTooLarge

import downloader

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Muhit o'zgaruvchilarini yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

dp = Dispatcher()

# YouTube so'rovlari uchun vaqtinchalik xotira kesh
# video_id -> {'url': url, 'title': title}
yt_cache: Dict[str, dict] = {}

URL_REGEX = re.compile(r'https?://[^\s]+')

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "👋 **Assalomu alaykum!**\n\n"
        "Men **Instagram, Facebook va YouTube** platformalaridan video va audio yuklab beruvchi botman.\n\n"
        "📥 **Qanday ishlatiladi?**\n"
        "Menga shunchaki video havolasini (linkini) yuboring:\n"
        "• 🔴 **YouTube** — Video sifatini tanlash (1080p, 720p, 480p, 360p) va **MP3 audio** ajratib olish imkoniyati bilan.\n"
        "• 🟣 **Instagram** — Reels, post va videolar.\n"
        "• 🔵 **Facebook** — Turli formatdagi videolar.\n\n"
        "Sinab ko'rish uchun hoziroq havola yuboring!"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "ℹ️ **Yordam va qo'llanma:**\n\n"
        "1. Instagram, Facebook yoki YouTube dagi video linkini nusxalang.\n"
        "2. Botga yuboring.\n"
        "3. YouTube bo'lsa, kerakli sifatni yoki 🎵 MP3 ovozni tanlang.\n"
        "4. Bot bir necha soniyada videoni yuklab beradi.\n\n"
        "⚠️ *Eslatma: Telegram botlar orqali yuboriladigan fayllarning maksimal hajmi 50 MB ni tashkil etadi.*"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text)
async def handle_incoming_link(message: types.Message):
    urls = URL_REGEX.findall(message.text)
    if not urls:
        await message.reply(
            "⚠️ Iltimos, to'g'ri video havolasini (YouTube, Instagram yoki Facebook) yuboring."
        )
        return

    url = urls[0]
    platform = downloader.detect_platform(url)

    if platform == "youtube":
        status_msg = await message.reply("🔍 YouTube video ma'lumotlari tahlil qilinmoqda...")
        try:
            info = await downloader.get_youtube_info(url)
            query_id = str(uuid.uuid4())[:8]
            yt_cache[query_id] = {
                'url': url,
                'title': info['title'],
                'duration': info['duration']
            }

            builder = InlineKeyboardBuilder()

            # Sifat tugmalari (har qatorda 2 tadan)
            qualities = info.get('qualities', [])
            for q in qualities:
                builder.button(
                    text=q['label'],
                    callback_data=f"yt:v:{query_id}:{q['height']}"
                )
            builder.adjust(2)

            # Faqat ovoz (MP3) tugmasi - alohida qatorda
            audio_text = info.get('audio_label', "🎵 Faqat ovoz (MP3)")
            builder.row(
                types.InlineKeyboardButton(
                    text=audio_text,
                    callback_data=f"yt:a:{query_id}"
                )
            )
            # Bekor qilish tugmasi
            builder.row(
                types.InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"yt:c:{query_id}"
                )
            )

            caption = (
                f"🎬 **{info['title']}**\n"
                f"⏱ Davomiyligi: {info['duration'] // 60} daqiqa {info['duration'] % 60} soniya\n\n"
                f"Iltimos, yuklash formatini yoki sifatini tanlang:"
            )

            thumb = info.get('thumbnail')
            await status_msg.delete()

            if thumb:
                try:
                    await message.reply_photo(
                        photo=thumb,
                        caption=caption,
                        reply_markup=builder.as_markup(),
                        parse_mode="Markdown"
                    )
                    return
                except Exception:
                    pass

            await message.reply(
                text=caption,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"YouTube ma'lumotlarini olishda xatolik: {e}")
            await status_msg.edit_text(f"❌ Videoni o'qib bo'lmadi yoki havola noto'g'ri.\nXatolik: {str(e)[:100]}")

    elif platform == "instagram":
        status_msg = await message.reply("⏳ Instagram videosi yuklanmoqda, iltimos kuting...")
        try:
            data = await downloader.download_instagram(url)
            file_path = data['file_path']

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                await status_msg.edit_text("❌ Instagram videoni yuklab bo'lmadi (akkaunt yopiq yoki video topilmadi).")
                return

            await status_msg.edit_text("📤 Telegramga yuborilmoqda...")
            video_file = types.FSInputFile(file_path)
            await message.reply_video(
                video=video_file,
                caption="🟣 **Instagram dan yuklab olindi**\n@Bot orqali yuklandi",
                parse_mode="Markdown"
            )
            await status_msg.delete()
            downloader.cleanup_file(file_path)
        except TelegramEntityTooLarge:
            await status_msg.edit_text("⚠️ Video hajmi 50 MB dan katta bo'lgani sababli Telegram orqali yuborib bo'lmadi.")
        except Exception as e:
            logger.error(f"Instagram yuklashda xatolik: {e}")
            await status_msg.edit_text(f"❌ Yuklab olishda xatolik yuz berdi: {str(e)[:100]}")

    elif platform == "facebook":
        status_msg = await message.reply("⏳ Facebook videosi yuklanmoqda, iltimos kuting...")
        try:
            data = await downloader.download_facebook(url)
            file_path = data['file_path']

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                await status_msg.edit_text("❌ Facebook videoni yuklab bo'lmadi (video yopiq guruhda yoki o'chirilgan bo'lishi mumkin).")
                return

            await status_msg.edit_text("📤 Telegramga yuborilmoqda...")
            video_file = types.FSInputFile(file_path)
            await message.reply_video(
                video=video_file,
                caption="🔵 **Facebook dan yuklab olindi**\n@Bot orqali yuklandi",
                parse_mode="Markdown"
            )
            await status_msg.delete()
            downloader.cleanup_file(file_path)
        except TelegramEntityTooLarge:
            await status_msg.edit_text("⚠️ Video hajmi 50 MB dan katta bo'lgani sababli Telegram orqali yuborib bo'lmadi.")
        except Exception as e:
            logger.error(f"Facebook yuklashda xatolik: {e}")
            await status_msg.edit_text(f"❌ Yuklab olishda xatolik yuz berdi: {str(e)[:100]}")

    else:
        await message.reply("⚠️ Noma'lum havola. Faqat YouTube, Instagram yoki Facebook havolalarini yuboring.")


@dp.callback_query(F.data.startswith("yt:"))
async def handle_youtube_callback(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    query_id = parts[2]

    await callback.answer()

    if action == "c":
        # Bekor qilish
        if query_id in yt_cache:
            del yt_cache[query_id]
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply("🚫 Yuklash bekor qilindi.")
        return

    if query_id not in yt_cache:
        await callback.message.reply("⚠️ Sessiya eskirgan. Iltimos, havolani qaytadan yuboring.")
        return

    item = yt_cache[query_id]
    url = item['url']
    title = item['title']

    if action == "v":
        # Video yuklash
        height = int(parts[3])
        status_msg = await callback.message.reply(f"⏳ YouTube videosi ({height}p) yuklanmoqda... (Hajmiga qarab bir necha soniya vaqt olishi mumkin)")
        try:
            data = await downloader.download_youtube_video(url, height)
            file_path = data['file_path']

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                await status_msg.edit_text("❌ Videoni yuklab bo'lmadi.")
                return

            size_mb = data['size'] / (1024 * 1024)
            if data['size'] > 50 * 1024 * 1024:
                await status_msg.edit_text(
                    f"⚠️ Video hajmi juda katta ({size_mb:.1f} MB).\n"
                    f"Telegram botlar faqat 50 MB gacha video yubora oladi.\n"
                    f"Iltimos, 480p yoki 360p sifatni tanlang yoki faqat MP3 audio yuklang."
                )
                downloader.cleanup_file(file_path)
                return

            await status_msg.edit_text("📤 Telegramga yuborilmoqda...")
            video_file = types.FSInputFile(file_path)
            caption_text = f"🎬 **{title}**\nSifat: {height}p"
            if data.get('compressed'):
                caption_text += "\n⚡ *Telegram 50MB limitiga moslab siqildi*"

            await callback.message.reply_video(
                video=video_file,
                caption=caption_text,
                parse_mode="Markdown"
            )
            await status_msg.delete()
            downloader.cleanup_file(file_path)
        except TelegramEntityTooLarge:
            await status_msg.edit_text("⚠️ Video hajmi 50 MB dan oshib ketdi. Telegram botlar faqat 50 MB gacha fayl yubora oladi. Kichikroq sifatni (masalan, 480p yoki 360p) tanlab ko'ring.")
        except Exception as e:
            logger.error(f"YouTube video yuklashda xatolik: {e}")
            await status_msg.edit_text(f"❌ Yuklashda xatolik yuz berdi: {str(e)[:120]}")

    elif action == "a":
        # Audio (MP3) ajratib olish
        status_msg = await callback.message.reply("🎵 Videodan audio (MP3) ajratib olinmoqda...")
        try:
            data = await downloader.download_youtube_audio(url)
            file_path = data['file_path']

            if not os.path.exists(file_path):
                await status_msg.edit_text("❌ Audioni ajratib bo'lmadi.")
                return

            await status_msg.edit_text("📤 Telegramga yuborilmoqda...")
            audio_file = types.FSInputFile(file_path)
            await callback.message.reply_audio(
                audio=audio_file,
                title=title,
                performer="YouTube Audio",
                caption=f"🎵 **{title}**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
            downloader.cleanup_file(file_path)
        except TelegramEntityTooLarge:
            await status_msg.edit_text("⚠️ Audio hajmi 50 MB dan katta bo'lgani sababli yuborib bo'lmadi.")
        except Exception as e:
            logger.error(f"YouTube audio yuklashda xatolik: {e}")
            await status_msg.edit_text(f"❌ Audio ajratishda xatolik yuz berdi: {str(e)[:120]}")

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or ":" not in BOT_TOKEN:
        print("\n" + "=" * 60)
        print("DIQQAT: To'g'ri BOT_TOKEN kiritilmadi!")
        print("Bot ishlashi uchun .env fayliga Telegram bot tokeningizni yozing:")
        print("BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz")
        print("(Tokenni Telegramdagi @BotFather orqali olasiz)")
        print("=" * 60 + "\n")
        return

    # bgutil PO Token serverini ishga tushirish
    import subprocess as _sp
    import shutil as _sh
    import os as _os
    _node = _sh.which("node")
    _bgutil_script = _os.path.expanduser(r"~\bgutil-ytdlp-pot-provider\server\build\main.js")
    if _node and _os.path.exists(_bgutil_script):
        try:
            _sp.Popen([_node, _bgutil_script],
                      stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                      creationflags=_sp.CREATE_NO_WINDOW if _os.name == 'nt' else 0)
            await asyncio.sleep(2)
            print("bgutil PO Token server ishga tushdi (port 4416)")
        except Exception as e:
            logger.warning(f"bgutil server ishga tushirilmadi: {e}")

    bot = Bot(token=BOT_TOKEN)
    cookie_status = " + Cookie fayli mavjud" if downloader.COOKIES_FILE.exists() else " (Cookie fayli topilmadi)"
    print(f"Bot ulandi: @arobiy_downloader_bot{cookie_status}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
