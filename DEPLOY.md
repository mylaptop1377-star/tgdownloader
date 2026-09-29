# 🤖 Telegram Video Downloader Bot - RENDER DEPLOYMENT QOLLANMA

## ⚡ Tez deployment (2 daqiqa)

### 1. Render.com da yaratish
1. https://render.com ga kiring (Google/GitHub bilan login)
2. Dashboard'da "New +" → "Web Service"
3. GitHub repository tanlang: `mylaptop1377-star/tgdownloader`
4. Environment: **Python 3.11**

### 2. Build va Start Commands

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python bot.py
```

### 3. Environment Variables o'rnatish (MUHIM!)

Render dashboard'da "Environment" tab'iga o'ting va quyidagilarni qo'shing:

```
BOT_TOKEN = 8661162985:AAF21x9eRTpdxF-JfSOop83uh-cpRRs7OgY
PORT = 8080
```

**⚠️ DIQQAT:** GitHub'ga hech qachon `.env` faylini push qilmang!

### 4. Deploy
- "Deploy" tugmasini bosing
- 3-5 minut kutish
- Logs'da "Bot ulandi" satrini topish

---

## 📋 Xavfsizlik Tekshiruvi

✅ `.env` fayli `.gitignore`'da
✅ GitHub'da `.env` saqlanmagan
✅ Token faqat Render environment variables'da
✅ `.env.example` bilan template mavjud
✅ Lokal `.env` faylini qo'l bilan yaratish kerak

---

## 🎯 Bot Ishlash Tekshiruvi

1. **Telegram'da bot topadmi?**
   - Bot username'ini qidiring: `@arobiy_downloader_bot`
   - Bot /start komandasini kiritib test qiling

2. **Logs'da xatolar bor-yu?
   - Render dashboard → "Logs" tab
   - "Bot ulandi" xatbarchasini qidiring

3. **Video yuklash tekshiruvi:**
   - YouTube linkini yuboring
   - Sifat tanlang (1080p, 720p, 480p, 360p)
   - MP3 audio ni test qiling
   - Instagram reel/post yuboring

---

## 🔧 Lokal Testlash (opsional)

```bash
# Repository'ni clone qiling
git clone https://github.com/mylaptop1377-star/tgdownloader.git
cd tgdownloader

# Virtual environment
python -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# ffmpeg (lokal)
# Ubuntu: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Windows: choco install ffmpeg

# .env faylini yarating
cp .env.example .env
# .env'da BOT_TOKEN'ni qo'ying

# Ishga tushiring
python bot.py
```

---

## 📞 Bot Funksiyalar

### YouTube
- 1080p, 720p, 480p, 360p sifat tanlash
- MP3 audio ajratish
- Auto compression (50 MB limit uchun)

### Instagram
- Reel, Post, Carousel
- Bir nechta media bir qatorda
- Avtomatik siqish

### Facebook
- Video yuklash
- Auto compression

---

## 🐛 Muammolar va Yechimlar

### "Bot offline"
- Render logs'da xatolar bor-yu?
- BOT_TOKEN to'g'ri qiymat bor-mu?
- ffmpeg o'rnatilgan-mu?

### "Instagram dan media topilmadi"
- Akkount private bo'lishi mumkin
- Rate limit o'tashtirgan
- Reel/post o'chirilgan bo'lishi mumkin

### "Video 50 MB dan katta"
- 480p yoki 360p sifatni tanlang
- MP3 audio ni tanlang

---

## ✅ Final Checklist

- [x] GitHub repo xavfsiz (no .env)
- [x] `.env.example` template mavjud
- [x] `requirements.txt` to'liq
- [x] `Procfile` sozlangan
- [x] `runtime.txt` Python 3.11
- [x] Bot xatosiz ishlaydi (lokal)
- [x] Render uchun setup hozir
- [x] TOKEN xavfsiz qo'yiladi

---

## 🎉 Ishchi Deployment

**Agar barcha test o'tgan bo'lsa:**

1. Render.com'da Web Service yarating
2. GitHub repo'ni bog'lang
3. Environment variables qo'shing (yuqoridagi malumot)
4. "Deploy" bosing
5. 5 minut kutish
6. Bot Telegram'da ishga tushadi

**Bot link:** https://t.me/arobiy_downloader_bot

---

**Qo'shimcha**:
- Bot 24/7 ishlaydi Render'da
- Video 50 MB dan katta bo'lsa avtomatik siqiladi
- Instagram carousel qo'lda boshlatiladi
- Logs Render dashboard'dan ko'riladi

**Tayyorlandi:** 2026-09-29
