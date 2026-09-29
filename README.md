# 🤖 Telegram Video Downloader Bot

**YouTube, Instagram, Facebook** platformalaridan video va audio yuklab oladigan Telegram bot.

## 🎯 Xususiyatlari

- ✅ **YouTube**: 1080p, 720p, 480p, 360p sifatlari + MP3 audio ajratish
- ✅ **Instagram**: Reel, Post, Carousel (bir nechta media)
- ✅ **Facebook**: Video yuklash
- ✅ **Automatic compression**: 50 MB limit uchun avtomatik siqish
- ✅ **Render deploy ready**: `.env` + `Procfile` bilan aniq deploy

## 📋 O'rnatish

### 1. Fayllarni yuklab olish
```bash
git clone https://github.com/mylaptop1377-star/tgdownloader.git
cd tgdownloader
```

### 2. Virtual environment yaratish
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\\Scripts\\activate  # Windows
```

### 3. Dependencies o'rnatish
```bash
pip install -r requirements.txt
```

### 4. ffmpeg o'rnatish
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

### 5. `.env` faylini yaratish
```bash
cp .env.example .env
```

Keyin `.env` faylida BOT_TOKEN ni o'zingizning Telegram bot tokeningiz bilan almashtirang:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
PORT=8080
```

**Bot tokenini qanday olish:**
1. Telegramda @BotFather botga yozing: `/start`
2. `/newbot` buyrugini yuboring
3. Bot nomini va username ni kiriting
4. Token olib, `.env` fayliga qo'ying

## 🚀 Ishga tushirish

### Lokal makinada
```bash
python bot.py
```

Bot shuki bo'lsa, quyidagi satrlar ko'rinadi:
```
Render healthcheck port 8080 da ishga tushdi
Bot ulandi: @arobiy_downloader_bot + Cookie fayli mavjud
```

### Render'da deploy qilish

#### 1. Render.com ga login qiling
https://render.com

#### 2. Yangi Web Service yaratish
- "New +" → "Web Service"
- GitHub repository ni tanlang: `mylaptop1377-star/tgdownloader`
- Environment ni tanlang: **Python 3.11**

#### 3. Sozlamalar
**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python bot.py
```

#### 4. Environment Variables o'rnatish
Render dashboard'da quyidagi **Environment Variables** qo'shing:

```
BOT_TOKEN = 123456789:ABCdefGhIJKlmNoPQRstuVWXyz
PORT = 8080
```

#### 5. Deploy
- "Deploy" tugmasini bosing
- 3-5 minut kutish
- Logs'da "Bot ulandi" satrini topish

## 🎮 Botdan foydalanish

### Telegram'da bot bilan suhbatlash

1. **YouTube video yuklash:**
   - YouTube linkini yuboring
   - Sifatni tanlang (1080p, 720p, 480p, 360p)
   - Yoki 🎵 MP3 audio ni tanlang

2. **Instagram media yuklash:**
   - Instagram link (reel, post, carousel) yuboring
   - Bot bir-birini qo'ldan kelib saqlashni o'tkazib, hammasini yuboradi

3. **Facebook video yuklash:**
   - Facebook video linkini yuboring
   - Bot video ni yuklab, Telegramga yuboradi

## 📝 Misol

```
Userе: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Bot: 🎬 Video nomini ko'rsatadi va sifat tugmalarini beradi

User: 720p ni tanladi
Bot: ⏳ Yuklanmoqda... 📤 Telegramga yuborilmoqda... ✅ Video jo'natildi
```

## 🛠️ Texnik tafsilotlar

- **Framework**: aiogram 3.x
- **Video downloader**: yt-dlp
- **Video processor**: FFmpeg
- **Async**: asyncio
- **Max file size**: 50 MB (Telegram API limit)
- **Auto compression**: Video 50 MB dan katta bo'lsa avtomatik siqiladi

## 📁 Fayllar tuzilishi

```
tgdownloader/
├── bot.py              # Main bot file
├── downloader.py       # YouTube/Instagram/Facebook download logic
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables example
├── Procfile           # Render deployment config
├── runtime.txt        # Python version for Render
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## 🐛 Muammolar

### "Instagram dan media topilmadi"
- Akkount yopiq yoki private bo'lishi mumkin
- Reel/post o'chirilgan bo'lishi mumkin
- Instagram API chegaralash (rate limit)

### "Video hajmi 50 MB dan oshdi"
- Kichikroq sifatni (360p yoki 480p) tanlang
- Yoki MP3 audio ni tanlang

### "FFmpeg topilmadi"
- ffmpeg o'rnatilganligini tekshiring
- `which ffmpeg` (Linux/Mac) yoki `where ffmpeg` (Windows) buyrugi ishlataing

## 📞 Yordam

- **Telegram**: @arobiy_downloader_bot
- **GitHub Issues**: Bug report va feature request uchun

## 📜 Litsenziya

MIT License - Bepul foydalanish uchun

---

**Mualliflar**: @mylaptop1377-star

**Oxirgi yangilanish**: 2026-09-29
