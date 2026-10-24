<div align="center">

# 🎬 Savora

### Download anything from Telegram — posts, stories, albums & private channels
### حمّل أي محتوى من تيليجرام — منشورات، ستوريات، ألبومات وقنوات خاصة

<br>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-cache-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Tests](https://img.shields.io/badge/tests-228%20passing-2EA44F?style=for-the-badge)

<br>

[English](#-english) · [العربية](#-العربية)

<br>

[![Telegram](https://img.shields.io/badge/Telegram-@K0__MG-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/K0_MG)
[![Instagram](https://img.shields.io/badge/Instagram-z0__28-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/z0_28)
[![TikTok](https://img.shields.io/badge/TikTok-@zt__tb-000000?style=for-the-badge&logo=tiktok&logoColor=white)](https://www.tiktok.com/@zt_tb)
[![YouTube](https://img.shields.io/badge/YouTube-@m7jn-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/@m7jn)

</div>

---

## 🇬🇧 English

Savora is a ready-to-run Telegram bot: send it a link, get the content back. It downloads through a logged-in Telegram account, so it can reach anything that account can see.

### ✨ Features

- 🔗 **Links** — posts (`t.me/channel/123`), private channels (`t.me/c/123/456`), stories (`t.me/user/s/5`), albums, and several links in one message
- 🎞 **All media** — photo, video, file, audio, voice, GIF, sticker, text (up to 2 GB per file)
- 📦 **Big files handled** — videos over ~49 MB are compressed with ffmpeg (up to 150 MB), otherwise split into ~45 MB parts
- ⚡ **Download queue** — parallel workers, live progress, cancel button, per-user pending limit
- 👑 **VIP with Telegram Stars** — daily / weekly / monthly plans, `/paysupport`, `/terms`, `/refund`
- 🎁 **Earn VIP** — share the bot, send a screenshot, the owner approves → 1 hour VIP
- 🔐 **Admin panel** — add/remove VIP, ban/unban, broadcast, stats, maintenance mode, caption footer & removed words, welcome media
- 🔑 **Downloader account login from the bot** — phone, QR or 2FA; session stored encrypted (Fernet)
- 🩺 **Health monitor** — checks the downloader account every 5 minutes and alerts the owner
- 🛡 **Anti-spam** and login rate limits
- 🌍 **Arabic & English** interface with animated emoji (falls back to normal emoji automatically)

| | Free | VIP |
|---|---|---|
| Downloads | 2, then renews after 2 days | Unlimited |
| Links per message | 2 | 10 |
| Queue | Normal | Priority |

### 📋 Requirements

| Needed | Where to get it |
|---|---|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) |
| ffmpeg | `apt install ffmpeg` / [ffmpeg.org](https://ffmpeg.org/download.html) |
| PostgreSQL | any provider (Railway, Supabase, local…) |
| Redis | any provider (Railway, Upstash, local…) |
| Bot token | [@BotFather](https://t.me/BotFather) |
| `API_ID` + `API_HASH` | [my.telegram.org](https://my.telegram.org) → API development tools |
| A Telegram account for downloading | logged in later from the admin panel |
| Your Telegram numeric ID (`ADMIN_ID`) | any "my id" bot, or the **🆔** button in Savora |

### 🚀 Quick start

```bash
git clone https://github.com/<your-username>/Savora.git
cd Savora
pip install -r requirements.txt
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python main.py
```

Put the generated key in `SESSION_ENCRYPTION_KEY`, fill in the rest of `.env`, then:

1. Send `/start` to your bot from the `ADMIN_ID` account
2. Open **🔐 Control Panel → 🔑 Downloader session** and log in the downloading account
3. Send any Telegram link

### ⚙️ Configuration (`.env`)

| Variable | Required | Description |
|---|:---:|---|
| `BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `ADMIN_ID` | ✅ | Owner's Telegram user ID |
| `API_ID` / `API_HASH` | ✅ | Telegram API credentials |
| `DATABASE_URL` | ✅ | PostgreSQL URL (`postgres://` or `postgresql://` is converted to asyncpg automatically) |
| `REDIS_URL` | ✅ | Redis URL |
| `SESSION_ENCRYPTION_KEY` | ✅ | Fernet key that encrypts the saved session |
| `DOWNLOADER_SESSION` | – | Telethon session string (alternative to logging in from the panel) |
| `ANIMATED_EMOJI` | – | `true` / `false` — needs Telegram Premium on the owner account |
| `VIP_STARS_D1` / `D7` / `D30` | – | VIP prices in Stars (default `50` / `250` / `700`) |
| `DOWNLOAD_WORKERS` | – | Parallel download workers (default `2`) |

### ☁️ Deploy on Railway

`Procfile` and `railpack.json` are included (the latter installs ffmpeg). Add PostgreSQL and Redis, set the variables above, and keep **Replicas = 1** — two copies with the same token will conflict.

### 🧪 Tests

```bash
python -m unittest discover -s tests -t .
```

### ⚠️ Notice

Use it only for content you have the right to access and save. Users are responsible for what they download.

---

<div dir="rtl">

## 🇮🇶 العربية

Savora بوت تيليجرام جاهز للتشغيل: ترسل له الرابط ويرجّع لك المحتوى. يحمّل عن طريق حساب تيليجرام مسجّل دخول، فيوصل لأي شي يقدر هذا الحساب يشوفه.

### ✨ المميزات

- 🔗 **الروابط** — منشورات (`t.me/channel/123`)، قنوات خاصة (`t.me/c/123/456`)، ستوريات (`t.me/user/s/5`)، ألبومات، وعدة روابط بنفس الرسالة
- 🎞 **كل أنواع الميديا** — صورة، فيديو، ملف، صوت، رسالة صوتية، GIF، ملصق، نص (لين 2 جيجا للملف)
- 📦 **الملفات الكبيرة** — الفيديو فوق ~49 ميجا يُضغط بـ ffmpeg (لين 150 ميجا)، وغير هيك يُقسّم لأجزاء ~45 ميجا
- ⚡ **طابور تحميل** — عمّال متوازين، تقدّم مباشر، زر إلغاء، وحد للطلبات المعلّقة لكل مستخدم
- 👑 **VIP بنجوم تيليجرام** — باقات يوم / أسبوع / شهر، مع `/paysupport` و `/terms` و `/refund`
- 🎁 **اربح VIP** — شارك البوت وأرسل لقطة شاشة، والمالك يوافق ← ساعة VIP
- 🔐 **لوحة تحكم** — إضافة/حذف VIP، حظر/فك حظر، بث، إحصائيات، وضع الصيانة، ذيل الكابشن والكلمات المحذوفة، ميديا الترحيب
- 🔑 **تسجيل دخول حساب التحميل من البوت** — برقم الهاتف أو QR أو 2FA، والجلسة تُخزَّن مشفّرة (Fernet)
- 🩺 **مراقبة الحساب** — فحص كل 5 دقايق وتنبيه للمالك
- 🛡 **حماية من السبام** وحدود لمحاولات تسجيل الدخول
- 🌍 **واجهة عربي وإنجليزي** مع إيموجي متحرك (يرجع لإيموجي عادي تلقائياً)

| | عادي | VIP |
|---|---|---|
| التحميلات | 2، وتتجدد بعد يومين | بلا حدود |
| الروابط بالرسالة | 2 | 10 |
| الطابور | عادي | أولوية |

### 📋 المتطلبات

| المطلوب | من وين |
|---|---|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) |
| ffmpeg | `apt install ffmpeg` / [ffmpeg.org](https://ffmpeg.org/download.html) |
| PostgreSQL | أي مزود (Railway, Supabase, محلي…) |
| Redis | أي مزود (Railway, Upstash, محلي…) |
| توكن البوت | [@BotFather](https://t.me/BotFather) |
| `API_ID` + `API_HASH` | [my.telegram.org](https://my.telegram.org) ← API development tools |
| حساب تيليجرام للتحميل | تسجّل دخوله بعدين من لوحة التحكم |
| أيدي حسابك (`ADMIN_ID`) | أي بوت "معرفي"، أو زر **🆔** بـ Savora |

### 🚀 التشغيل السريع

```bash
git clone https://github.com/<your-username>/Savora.git
cd Savora
pip install -r requirements.txt
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python main.py
```

حط المفتاح الطالع بـ `SESSION_ENCRYPTION_KEY`، واملأ باقي `.env`، وبعدها:

1. أرسل `/start` للبوت من حساب `ADMIN_ID`
2. افتح **🔐 لوحة التحكم ← 🔑 جلسة التحميل** وسجّل دخول حساب التحميل
3. أرسل أي رابط تيليجرام

### ⚙️ الإعدادات (`.env`)

| المتغير | إلزامي | الوصف |
|---|:---:|---|
| `BOT_TOKEN` | ✅ | توكن البوت من @BotFather |
| `ADMIN_ID` | ✅ | أيدي المالك |
| `API_ID` / `API_HASH` | ✅ | مفاتيح تيليجرام API |
| `DATABASE_URL` | ✅ | رابط PostgreSQL (`postgres://` أو `postgresql://` يتحوّل تلقائياً لـ asyncpg) |
| `REDIS_URL` | ✅ | رابط Redis |
| `SESSION_ENCRYPTION_KEY` | ✅ | مفتاح Fernet لتشفير الجلسة المحفوظة |
| `DOWNLOADER_SESSION` | – | سترنغ جلسة Telethon (بديل تسجيل الدخول من اللوحة) |
| `ANIMATED_EMOJI` | – | `true` / `false` — يحتاج Telegram Premium بحساب المالك |
| `VIP_STARS_D1` / `D7` / `D30` | – | أسعار VIP بالنجوم (الافتراضي `50` / `250` / `700`) |
| `DOWNLOAD_WORKERS` | – | عدد عمّال التحميل (الافتراضي `2`) |

### ☁️ النشر على Railway

ملفات `Procfile` و `railpack.json` موجودة (الثاني يثبّت ffmpeg). أضف PostgreSQL و Redis، واضبط المتغيرات فوق، وخلّ **Replicas = 1** — نسختين بنفس التوكن يتعارضون.

### 🧪 الاختبارات

```bash
python -m unittest discover -s tests -t .
```

### ⚠️ تنبيه

استخدمه فقط للمحتوى الي من حقك توصله وتحفظه. المستخدم مسؤول عن الي يحمّله.

</div>

---

<div align="center">

**Made with ❤️ in Iraq 🇮🇶 — by [@K0_MG](https://t.me/K0_MG)**

</div>
