import asyncio, html, logging, os, random, time
from io import BytesIO
from typing import Optional

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configured Bot Token & Admin ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "8649227717:AAEe4gOxmKnwOxd7J4earHlL1I241aiqz4w")
ADMIN_CHAT_ID = "8402780798"

# Cooldown delay in seconds between uploads to prevent API spam/down
UPLOAD_COOLDOWN = 10 

USER_COOLDOWN = {}
CAPTCHA_DATA = {}
CAPTCHA_SOLVED = set()
BOT_USERS = set()
RECENT_UPLOADS = []
TOTAL_UPLOADS = 0
USER_LOCKS = {}


def user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in USER_LOCKS:
        USER_LOCKS[user_id] = asyncio.Lock()
    return USER_LOCKS[user_id]


# ---------------- 10 PERMANENT & STABLE IMAGE APIS ----------------

async def upload_catbox(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("reqtype", "fileupload")
        d.add_field("fileToUpload", BytesIO(b), filename="image.jpg")
        async with s.post("https://catbox.moe/user/api.php", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            t = await r.text()
            return t.strip() if r.status == 200 and t.strip().startswith("http") else None
    except Exception:
        return None


async def upload_telegraph(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("file", BytesIO(b), filename="image.jpg", content_type="image/jpeg")
        async with s.post("https://telegra.ph/upload", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                x = await r.json(content_type=None)
                if isinstance(x, list) and x and x[0].get("src"):
                    return "https://telegra.ph" + x[0]["src"]
    except Exception:
        pass
    return None


async def upload_0x0(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("file", BytesIO(b), filename="image.jpg", content_type="image/jpeg")
        async with s.post("https://0x0.st", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            t = await r.text()
            return t.strip() if r.status == 200 and t.strip().startswith("http") else None
    except Exception:
        return None


async def upload_freeimage(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("key", "6d207e02198a847aa98d0a2a901485a5")
        d.add_field("action", "upload")
        d.add_field("format", "json")
        d.add_field("source", BytesIO(b), filename="image.jpg")
        async with s.post("https://freeimage.host/api/1/upload", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                x = await r.json(content_type=None)
                if "image" in x and "url" in x["image"]:
                    return x["image"]["url"]
    except Exception:
        pass
    return None


async def upload_imgbb(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("key", "6d207e02198a847aa98d0a2a901485a5")
        d.add_field("image", BytesIO(b), filename="image.jpg")
        async with s.post("https://api.imgbb.com/1/upload", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                x = await r.json(content_type=None)
                if "data" in x and "url" in x["data"]:
                    return x["data"]["url"]
    except Exception:
        pass
    return None


async def upload_imghippo(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("api_key", "6d207e02198a847aa98d0a2a901485a5")
        d.add_field("file", BytesIO(b), filename="image.jpg")
        async with s.post("https://api.imghippo.com/v1/upload", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                x = await r.json(content_type=None)
                if x.get("success") and "data" in x:
                    return x["data"]["url"]
    except Exception:
        pass
    return None


async def upload_envs_sh(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("file", BytesIO(b), filename="image.jpg")
        async with s.post("https://envs.sh", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            t = await r.text()
            return t.strip() if r.status == 200 and t.strip().startswith("http") else None
    except Exception:
        return None


async def upload_pixeldrain(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("file", BytesIO(b), filename="image.jpg")
        async with s.post("https://pixeldrain.com/api/file", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status in [200, 201]:
                x = await r.json(content_type=None)
                if x.get("success"):
                    return f"https://pixeldrain.com/api/file/{x['id']}"
    except Exception:
        pass
    return None


async def upload_postimages(s, b: bytes) -> Optional[str]:
    try:
        d = aiohttp.FormData()
        d.add_field("optsize", "0")
        d.add_field("file", BytesIO(b), filename="image.jpg")
        async with s.post("https://postimages.org/json/rr", data=d, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                x = await r.json(content_type=None)
                if "url" in x:
                    return x["url"]
    except Exception:
        pass
    return None


async def upload_imgur(s, b: bytes) -> Optional[str]:
    try:
        headers = {"Authorization": "Client-ID 5442572f3e18930"}
        d = aiohttp.FormData()
        d.add_field("image", BytesIO(b), filename="image.jpg")
        async with s.post("https://api.imgur.com/3/image", data=d, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                x = await r.json(content_type=None)
                if x.get("success") and "data" in x:
                    return x["data"]["link"]
    except Exception:
        pass
    return None


async def upload_multi(b: bytes) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=20),
        headers=headers,
    ) as s:
        tasks = [
            asyncio.create_task(upload_catbox(s, b)),
            asyncio.create_task(upload_telegraph(s, b)),
            asyncio.create_task(upload_freeimage(s, b)),
            asyncio.create_task(upload_imgbb(s, b)),
            asyncio.create_task(upload_imghippo(s, b)),
            asyncio.create_task(upload_0x0(s, b)),
            asyncio.create_task(upload_envs_sh(s, b)),
            asyncio.create_task(upload_pixeldrain(s, b)),
            asyncio.create_task(upload_postimages(s, b)),
            asyncio.create_task(upload_imgur(s, b)),
        ]
        
        try:
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    if isinstance(result, str) and result.startswith("http"):
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        return result
                except Exception:
                    continue
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            
    return None


# ---------------- CAPTCHA ----------------

def new_captcha(user_id: int):
    kind = random.choice(["add", "sub", "mul", "emoji"])

    if kind == "add":
        a, b = random.randint(2, 19), random.randint(2, 19)
        answer, question = a + b, f"🔢 {a} + {b} = ?"
    elif kind == "sub":
        a = random.randint(10, 30)
        b = random.randint(1, a - 1)
        answer, question = a - b, f"➖ {a} − {b} = ?"
    elif kind == "mul":
        a, b = random.randint(2, 9), random.randint(2, 9)
        answer, question = a * b, f"✖️ {a} × {b} = ?"
    else:
        e = random.choice(["🍎", "⭐", "🔵", "🍋", "🐟", "❤️", "🟢"])
        n = random.randint(3, 8)
        answer, question = n, " ".join([e] * n) + f"\n\n👀 উপরের {e} কয়টি আছে?"

    CAPTCHA_DATA[user_id] = {"answer": answer, "time": time.time()}
    opts = {answer}
    while len(opts) < 4:
        opts.add(max(0, answer + random.randint(-4, 4)))
    opts = list(opts)
    random.shuffle(opts)
    keyboard = [[InlineKeyboardButton(str(x), callback_data=f"captcha|{x}") for x in opts]]
    return question, InlineKeyboardMarkup(keyboard)


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    if user.is_bot:
        await update.message.reply_text("⛔ Telegram bot account ব্যবহার করা যাবে না।")
        return

    BOT_USERS.add(user.id)

    if str(user.id) != ADMIN_CHAT_ID:
        CAPTCHA_SOLVED.discard(user.id)
        question, keyboard = new_captcha(user.id)
        await update.message.reply_text(
            "🛡️ <b>SECURITY CHECK</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "নিচের প্রশ্নের সঠিক উত্তরে ক্লিক করুন।\n\n"
            f"<b>{question}</b>\n\n"
            "🔐 প্রতিবার নতুন প্রশ্ন আসবে।",
            parse_mode="HTML", reply_markup=keyboard)
        return

    await main_panel(update, user)


async def main_panel(update: Update, user):
    text = (
        f"👑 <b>স্বাগতম, {html.escape(user.first_name)}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>ATIKUL ULTRA IMAGE CDN</b>\n\n"
        "📸 ছবি পাঠান → ১০টি স্থায়ী এপিআই দিয়ে direct link পাবেন।\n\n"
        "🚀 Fast • Multi-Server • Permanent Direct Link"
    )
    keys = [[InlineKeyboardButton("📘 ব্যবহার করার নিয়ম", callback_data="help")]]
    if str(user.id) == ADMIN_CHAT_ID:
        keys.append([InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin")])
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keys))


# ---------------- PHOTO HANDLE WITH TIMING ----------------

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_UPLOADS
    message = update.message
    user = message.from_user if message else None
    if not message or not user or user.is_bot:
        return

    uid = user.id
    BOT_USERS.add(uid)

    if str(uid) != ADMIN_CHAT_ID and uid not in CAPTCHA_SOLVED:
        await message.reply_text("⚠️ আগে /start দিয়ে Human Verification সম্পন্ন করুন।")
        return

    # ⏳ COOLDOWN CHECKING (টাইমিং কাউন্টডাউন)
    now = time.time()
    last_upload = USER_COOLDOWN.get(uid, 0)
    time_passed = now - last_upload

    if time_passed < UPLOAD_COOLDOWN:
        remaining = int(UPLOAD_COOLDOWN - time_passed)
        await message.reply_text(
            f"⏳ <b>অনুগ্রহ করে একটু অপেক্ষা করুন!</b>\n"
            f"এপিআই ডাউন বা ব্লক হওয়া রোধ করতে টাইমার চালু আছে।\n\n"
            f"⏱️ আর <b>{remaining} সেকেন্ড</b> পর আবার ছবি আপলোড করতে পারবেন।",
            parse_mode="HTML"
        )
        return

    # Lock and update time
    async with user_lock(uid):
        USER_COOLDOWN[uid] = time.time()

        status = await message.reply_text(
            "╔══════════════════════╗\n"
            "   🚀 <b>ATIKUL IMAGE ENGINE</b>\n"
            "╚══════════════════════╝\n\n"
            "🔍 ছবি গ্রহণ করা হচ্ছে...",
            parse_mode="HTML")

        if message.photo:
            obj = message.photo[-1]
            tg_file = await obj.get_file()
            size = obj.file_size or 0
        elif message.document and (message.document.mime_type or "").startswith("image/"):
            tg_file = await message.document.get_file()
            size = message.document.file_size or 0
        else:
            await status.edit_text("❌ শুধু ছবি পাঠান।")
            return

        steps = [
            "🟦 <b>01 / 05</b> ▰▱▱▱▱  ছবি প্রস্তুত...",
            "🟩 <b>02 / 05</b> ▰▰▱▱▱  Image engine চালু...",
            "🟨 <b>03 / 05</b> ▰▰▰▱▱  স্থায়ী এপিআই-তে পাঠানো হচ্ছে...",
            "🟧 <b>04 / 05</b> ▰▰▰▰▱  দ্রুততম response খোঁজা হচ্ছে...",
        ]
        for step in steps:
            try:
                await status.edit_text(
                    "╔══════════════════════╗\n"
                    "   ✨ <b>PROCESSING</b>\n"
                    "╚══════════════════════╝\n\n" + step,
                    parse_mode="HTML")
            except Exception:
                pass
            await asyncio.sleep(0.18)

        raw = await tg_file.download_as_bytearray()
        await status.edit_text(
            "🟪 <b>05 / 05</b> ▰▰▰▰▰\n\n"
            "⚡ Permanent link তৈরি হচ্ছে...",
            parse_mode="HTML")

        link = await upload_multi(bytes(raw))

        if not link:
            await status.edit_text(
                "❌ <b>কোনো upload server এই মুহূর্তে সফল হয়নি।</b>\n"
                "কিছুক্ষণ পরে আবার চেষ্টা করুন।", parse_mode="HTML")
            return

        TOTAL_UPLOADS += 1
        RECENT_UPLOADS.insert(0, {
            "user": f"@{user.username}" if user.username else user.first_name,
            "user_id": uid, "link": link, "size_kb": round(size / 1024, 2)
        })
        del RECENT_UPLOADS[20:]

        keys = [
            [InlineKeyboardButton("🔗 লিঙ্ক কপি/দেখুন", callback_data=f"link|{link}")],
            [InlineKeyboardButton("🌐 ব্রাউজারে ওপেন", url=link)],
        ]
        await status.edit_text(
            "╔══════════════════════════╗\n"
            "   🎉 <b>UPLOAD COMPLETE</b>\n"
            "╚══════════════════════════╝\n\n"
            "✅ Permanent Direct Image Link প্রস্তুত।\n\n"
            f"🔗 <code>{html.escape(link)}</code>\n\n"
            f"⏱️ <i>পরবর্তী আপলোড {UPLOAD_COOLDOWN} সেকেন্ড পর করতে পারবেন।</i>",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keys))

        try:
            await message.delete()
        except Exception:
            pass


# ---------------- BUTTONS ----------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    user = q.from_user
    if user.is_bot:
        await q.answer("⛔ Bot accounts are not supported.", show_alert=True)
        return

    parts = q.data.split("|", 1)
    action = parts[0]

    if action == "captcha":
        try:
            selected = int(parts[1])
        except Exception:
            await q.answer("❌ Invalid answer.", show_alert=True)
            return

        record = CAPTCHA_DATA.get(user.id)
        if not record or time.time() - record["time"] > 120:
            question, keyboard = new_captcha(user.id)
            await q.answer("⏱️ পুরোনো CAPTCHA শেষ। নতুনটি দেওয়া হয়েছে।", show_alert=True)
            await q.message.edit_text(
                "🛡️ <b>নতুন Security Check</b>\n\n" + question,
                parse_mode="HTML", reply_markup=keyboard)
            return

        if selected == record["answer"]:
            CAPTCHA_SOLVED.add(user.id)
            CAPTCHA_DATA.pop(user.id, None)
            await q.answer("✅ Verification সফল!")
            try:
                await q.message.delete()
            except Exception:
                pass
            await q.message.chat.send_message(
                "✅ <b>Verification সম্পন্ন!</b>\n\n📸 এখন আপনার ছবি পাঠান।",
                parse_mode="HTML")
        else:
            question, keyboard = new_captcha(user.id)
            await q.answer("❌ ভুল! নতুন প্রশ্ন দেওয়া হয়েছে।", show_alert=True)
            await q.message.edit_text(
                "🛡️ <b>আবার চেষ্টা করুন</b>\n\n" + question,
                parse_mode="HTML", reply_markup=keyboard)

    elif action == "help":
        await q.answer()
        await q.message.reply_text(
            "📘 <b>ব্যবহার বিধি:</b>\n\n"
            "1️⃣ /start দিন\n"
            "2️⃣ Security Check সম্পন্ন করুন\n"
            "3️⃣ ছবি পাঠান\n"
            "4️⃣ ১০টি স্থায়ী এপিআই থেকে সরাসরি ডিরেক্ট লিঙ্ক পাবেন\n"
            "5️⃣ প্রতিবার আপলোডের পর ১০ সেকেন্ড টাইমার থাকবে।",
            parse_mode="HTML")

    elif action == "link":
        if len(parts) != 2:
            await q.answer("❌ Link পাওয়া যায়নি।", show_alert=True)
            return
        await q.answer("✅ Link প্রস্তুত!")
        await q.message.reply_text(
            f"🔗 <b>Direct Image Link:</b>\n\n<code>{html.escape(parts[1])}</code>",
            parse_mode="HTML")

    elif action == "admin":
        if str(user.id) != ADMIN_CHAT_ID:
            await q.answer("❌ Admin only.", show_alert=True)
            return
        await q.answer()
        await q.message.reply_text(
            "🛠️ <b>ADMIN PANEL</b>\n"
            f"👥 Total Users: <code>{len(BOT_USERS)}</code>\n"
            f"📸 Total Uploads: <code>{TOTAL_UPLOADS}</code>\n\n"
            "<code>/broadcast আপনার মেসেজ</code>",
            parse_mode="HTML")


# ---------------- BROADCAST ----------------

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or str(update.effective_user.id) != ADMIN_CHAT_ID:
        return
    if not context.args:
        await update.message.reply_text("ব্যবহার: /broadcast আপনার মেসেজ")
        return
    text = " ".join(context.args)
    sent = 0
    for uid in list(BOT_USERS):
        try:
            await context.bot.send_message(
                uid, f"📢 <b>Admin Notice</b>\n\n{html.escape(text)}",
                parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"✅ {sent} জনকে পাঠানো হয়েছে।")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception", exc_info=context.error)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_photo))
    app.add_error_handler(error_handler)

    logger.info("Atikul Ultra Image Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
            
