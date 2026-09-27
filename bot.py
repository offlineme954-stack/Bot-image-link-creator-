import asyncio
import logging
import random
import time
from io import BytesIO
from typing import Optional

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config Credentials
BOT_TOKEN = "8649227717:AAEj9lgvTmu87PRP8gStEPkrx0ZZODbPifs"
ADMIN_CHAT_ID = "8402780798"
REQUIRED_CHANNEL = "@atiqul_services_bot"

# Global Memory Storage
USER_COOLDOWN = {}
CAPTCHA_SOLVED = set()  # Verified Users
CAPTCHA_DATA = {}      # User Captcha Math Storage
BOT_USERS = set()       # All Unique Users for Broadcast
TOTAL_UPLOADS = 0
RECENT_UPLOADS = []


# ---------------- 12 DIRECT IMAGE API HANDLERS ---------------- #

async def upload_catbox(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("reqtype", "fileupload")
        data.add_field("fileToUpload", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://catbox.moe/user/api.php", data=data, timeout=7) as res:
            text = await res.text()
            if res.status == 200 and text.startswith("http"):
                return text.strip()
    except Exception:
        pass
    return None

async def upload_telegraph(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("file", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://telegra.ph/upload", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if isinstance(json_data, list) and "src" in json_data[0]:
                    return "https://telegra.ph" + json_data[0]["src"]
    except Exception:
        pass
    return None

async def upload_freeimage(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("key", "6d207e02198a847aa98d0a2a901485a5")
        data.add_field("action", "upload")
        data.add_field("format", "json")
        data.add_field("source", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://freeimage.host/api/1/upload", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if "image" in json_data and "url" in json_data["image"]:
                    return json_data["image"]["url"]
    except Exception:
        pass
    return None

async def upload_imgbb(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("key", "6d207e02198a847aa98d0a2a901485a5")
        data.add_field("image", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://api.imgbb.com/1/upload", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if "data" in json_data and "url" in json_data["data"]:
                    return json_data["data"]["url"]
    except Exception:
        pass
    return None

async def upload_imghippo(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("api_key", "6d207e02198a847aa98d0a2a901485a5")
        data.add_field("file", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://api.imghippo.com/v1/upload", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if json_data.get("success") and "data" in json_data:
                    return json_data["data"]["url"]
    except Exception:
        pass
    return None

async def upload_envs_sh(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("file", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://envs.sh", data=data, timeout=7) as res:
            text = await res.text()
            if res.status == 200 and text.startswith("http"):
                return text.strip()
    except Exception:
        pass
    return None

async def upload_pomf(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("files[]", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://pomf.lain.la/upload.php", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if json_data.get("success") and "files" in json_data:
                    return json_data["files"][0]["url"]
    except Exception:
        pass
    return None

async def upload_pixeldrain(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("file", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://pixeldrain.com/api/file", data=data, timeout=7) as res:
            if res.status in [200, 201]:
                json_data = await res.json()
                if json_data.get("success"):
                    return f"https://pixeldrain.com/api/file/{json_data['id']}"
    except Exception:
        pass
    return None

async def upload_litterbox(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("reqtype", "fileupload")
        data.add_field("time", "1h")
        data.add_field("fileToUpload", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://litterbox.catbox.moe/resources/internals/api.php", data=data, timeout=7) as res:
            text = await res.text()
            if res.status == 200 and text.startswith("http"):
                return text.strip()
    except Exception:
        pass
    return None

async def upload_quax(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("files[]", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://quax.to/upload.php", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if json_data.get("success") and "files" in json_data:
                    return json_data["files"][0]["url"]
    except Exception:
        pass
    return None

async def upload_fileio(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("file", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://file.io", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if json_data.get("success"):
                    return json_data.get("link")
    except Exception:
        pass
    return None

async def upload_tmpfiles(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("file", BytesIO(file_bytes), filename="image.jpg")
        async with session.post("https://tmpfiles.org/api/v1/upload", data=data, timeout=7) as res:
            if res.status == 200:
                json_data = await res.json()
                if json_data.get("status") == "success":
                    url = json_data["data"]["url"]
                    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception:
        pass
    return None


async def upload_image_multi_api(file_bytes: bytes) -> Optional[str]:
    """Concurrent Engine calling 12 APIs at once"""
    async with aiohttp.ClientSession() as session:
        tasks = [
            upload_catbox(session, file_bytes),
            upload_telegraph(session, file_bytes),
            upload_freeimage(session, file_bytes),
            upload_imgbb(session, file_bytes),
            upload_imghippo(session, file_bytes),
            upload_envs_sh(session, file_bytes),
            upload_pomf(session, file_bytes),
            upload_pixeldrain(session, file_bytes),
            upload_litterbox(session, file_bytes),
            upload_quax(session, file_bytes),
            upload_fileio(session, file_bytes),
            upload_tmpfiles(session, file_bytes)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, str) and res.startswith("http"):
                return res
    return None


# ---------------- UTILITY FUNCTIONS ---------------- #

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        logger.error(f"Sub check error: {e}")
        return True
    return False

def generate_captcha(user_id: int):
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    ans = num1 + num2
    CAPTCHA_DATA[user_id] = ans
    return num1, num2, ans


# ---------------- COMMAND & CAPTCHA HANDLERS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    BOT_USERS.add(user.id)

    # 1. Human Verification / Captcha Check
    if user.id not in CAPTCHA_SOLVED and str(user.id) != ADMIN_CHAT_ID:
        num1, num2, ans = generate_captcha(user.id)
        
        # Make Inline Options
        options = [ans, ans + 1, ans - 1, ans + 2]
        random.shuffle(options)
        
        buttons = []
        row = []
        for opt in options:
            row.append(InlineKeyboardButton(str(opt), callback_data=f"captcha_val|{opt}"))
        buttons.append(row)

        await update.message.reply_text(
            f"🛡️ <b>হিউম্যান ভেরিফিকেশন (Human Verification):</b>\n\n"
            f"আপনি যে একজন মানুষ তা নিশ্চিত করতে নিচের হিসাবটির সঠিক উত্তরে ক্লিক করুন:\n\n"
            f"❓ <b>{num1} + {num2} = কত?</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # 2. Force Subscribe Check
    is_subbed = await check_subscription(user.id, context)
    if not is_subbed:
        keyboard = [
            [InlineKeyboardButton("📢 Join Official Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verified / Joined", callback_data="check_sub_again")]
        ]
        await update.message.reply_text(
            f"⚠️ <b>বটটি ব্যবহার করতে চ্যানেল জয়েন করুন!</b>\n\n"
            f"আমাদের চ্যানেল <b>{REQUIRED_CHANNEL}</b> এ জয়েন করে 'Verified / Joined' বাটনে চাপ দিন।",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Main Welcome Panel
    welcome_text = (
        f"👑 <b>স্বাগতম, {user.first_name}!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <b>Atikul Ultra Direct Image CDN Bot</b>\n\n"
        "📸 <b>যেকোনো ছবি এখনই সেন্ড করুন!</b>\n"
        "ওয়েবসাইট ও নিউজ কার্ডে সরাসরি সাপোর্ট করে এমন ডাইরেক্ট এক্সটেনশন সহ ছবি লিঙ্ক পেয়ে যাবেন।\n\n"
        "⚡ <i>১২টি হাই-স্পিড সিডিএন সার্ভার যুক্ত করা আছে!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [InlineKeyboardButton("📘 ব্যবহার করার নিয়ম", callback_data="btn_instructions")],
        [
            InlineKeyboardButton("📢 চ্যানেল", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"),
            InlineKeyboardButton("👨‍💻 অ্যাডমিন", url=f"tg://user?id={ADMIN_CHAT_ID}")
        ]
    ]

    if str(user.id) == ADMIN_CHAT_ID:
        keyboard.append([InlineKeyboardButton("🛠️ Admin Panel & Broadcast", callback_data="open_admin_panel")])

    await update.message.reply_text(
        welcome_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- PHOTO PROCESSOR WITH ANIMATION ---------------- #

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_UPLOADS, RECENT_UPLOADS
    message = update.message
    user_id = message.from_user.id
    BOT_USERS.add(user_id)

    # Captcha Check
    if user_id not in CAPTCHA_SOLVED and str(user_id) != ADMIN_CHAT_ID:
        await message.reply_text("⚠️ <b>অনুগ্রহ করে আগে স্টার্ট দিয়ে সঠিকভাবে ভেরিফিকেশন সম্পন্ন করুন!</b> /start", parse_mode="HTML")
        return

    # Force Sub Check
    is_subbed = await check_subscription(user_id, context)
    if not is_subbed:
        await message.reply_text("⚠️ <b>চ্যানেলে জয়েন করে /start দিন!</b>", parse_mode="HTML")
        return

    # Rate Limiting
    current_time = time.time()
    if user_id in USER_COOLDOWN and current_time - USER_COOLDOWN[user_id] < 2:
        await message.reply_text("⚠️ <b>অপেক্ষা করুন! ১-২ সেকেন্ড পর আবার চেষ্টা করুন।</b>", parse_mode="HTML")
        return
    USER_COOLDOWN[user_id] = current_time

    if message.photo:
        photo_obj = message.photo[-1]
        photo_file = await photo_obj.get_file()
        file_size_kb = round(photo_obj.file_size / 1024, 2) if photo_obj.file_size else 0
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        photo_file = await message.document.get_file()
        file_size_kb = round(message.document.file_size / 1024, 2) if message.document.file_size else 0
    else:
        await message.reply_text("❌ <b>অনুগ্রহ করে একটি ছবি ফাইল পাঠাইন!</b>", parse_mode="HTML")
        return

    # Interactive Processing Animation
    status_msg = await message.reply_text("🔄 <i>ইমেজ প্রসেসিং শুরু হচ্ছে...</i>", parse_mode="HTML")
    
    animations = [
        "⏳ <b>[■□□□□□□□□□] 10%</b> - ফাইল রিড করা হচ্ছে...",
        "⚡ <b>[███□□□□□□□] 35%</b> - সিডিএন এপিআই কানেক্ট হচ্ছে...",
        "🚀 <b>[███████□□□] 75%</b> - ডাইরেক্ট লিঙ্ক তৈরি হচ্ছে...",
        "✨ <b>[██████████] 100%</b> - আপলোড সম্পন্ন!"
    ]

    for anim in animations[:2]:
        await asyncio.sleep(0.3)
        try:
            await status_msg.edit_text(anim, parse_mode="HTML")
        except Exception:
            pass

    file_bytes = await photo_file.download_as_bytearray()
    
    # Send remaining animation step
    try:
        await status_msg.edit_text(animations[2], parse_mode="HTML")
    except Exception:
        pass

    direct_link = await upload_image_multi_api(file_bytes)

    if direct_link:
        TOTAL_UPLOADS += 1
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        RECENT_UPLOADS.insert(0, {
            "user": user_info,
            "user_id": user_id,
            "link": direct_link,
            "size": file_size_kb
        })
        if len(RECENT_UPLOADS) > 20:
            RECENT_UPLOADS.pop()

        keyboard = [
            [InlineKeyboardButton("🔗 ডাইরেক্ট ছবি লিঙ্ক কপি করুন", callback_data=f"get_link|{direct_link}")],
            [InlineKeyboardButton("🌐 ব্রাউজারে ওপেন করুন", url=direct_link)]
        ]

        await status_msg.edit_text(
            f"🎉 <b>আপনার ডাইরেক্ট ইমেজ লিঙ্ক তৈরি হয়েছে!</b>\n\n"
            f"<code>{direct_link}</code>\n\n"
            f"🌐 <i>ওয়েবসাইট ও নিউজ কার্ডে শতভাগ কাজ করবে।</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Auto-delete original image message from user
        try:
            await message.delete()
        except Exception:
            pass

    else:
        await status_msg.edit_text("❌ <b>সবগুলো সার্ভার ব্যস্ত থাকার কারণে আপলোড ব্যর্থ হয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।</b>", parse_mode="HTML")


# ---------------- ADMIN BROADCAST & BUTTON HANDLERS ---------------- #

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text("⚠️ <b>ব্যবহার করার নিয়ম:</b>\n`/broadcast আপনার মেসেজ লিখুন`", parse_mode="Markdown")
        return

    msg = " ".join(context.args)
    count = 0
    await update.message.reply_text("📢 <b>ব্রডকাস্ট শুরু হচ্ছে...</b>", parse_mode="HTML")

    for u_id in list(BOT_USERS):
        try:
            await context.bot.send_message(chat_id=u_id, text=f"📢 <b>অ্যাডমিন নোটিশ:</b>\n\n{msg}", parse_mode="HTML")
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(f"✅ <b>সফলভাবে {count} জন ইউজারের কাছে মেসেজ পাঠানো হয়েছে!</b>", parse_mode="HTML")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("|")
    action = data[0]

    # Captcha Validation
    if action == "captcha_val":
        val = int(data[1])
        if CAPTCHA_DATA.get(user_id) == val:
            CAPTCHA_SOLVED.add(user_id)
            await query.answer("✅ আপনার উত্তর সঠিক হয়েছে! ধন্যবাদ।", show_alert=True)
            await query.message.delete()
            # Redirect to start
            await start(update, context)
        else:
            await query.answer("❌ ভুল উত্তর! আবার চেষ্টা করুন।", show_alert=True)
            num1, num2, ans = generate_captcha(user_id)
            options = [ans, ans + 1, ans - 1, ans + 2]
            random.shuffle(options)
            buttons = [[InlineKeyboardButton(str(opt), callback_data=f"captcha_val|{opt}") for opt in options]]
            await query.message.edit_text(
                f"🛡️ <b>ভুল উত্তর দিয়েছেন! আবার চেষ্টা করুন:</b>\n\n❓ <b>{num1} + {num2} = কত?</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif action == "check_sub_again":
        is_subbed = await check_subscription(user_id, context)
        if is_subbed:
            await query.answer("✅ চ্যানেলে জয়েন সফল হয়েছে!", show_alert=True)
            await query.message.delete()
            await start(update, context)
        else:
            await query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

    elif action == "btn_instructions":
        await query.answer()
        await query.message.reply_text("📸 <b>আপনার যেকোনো ছবি চ্যাটে পাঠালেই ডাইরেক্ট লিংক পেয়ে যাবেন!</b>", parse_mode="HTML")

    elif action == "get_link":
        link = data[1]
        await query.answer("✅ লিংক প্রস্তুত!", show_alert=False)
        await query.message.reply_text(f"🔗 <b>আপনার লিঙ্ক:</b>\n\n<code>{link}</code>", parse_mode="HTML")

    elif action == "open_admin_panel":
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer("❌ আপনি অ্যাডমিন নন!", show_alert=True)
            return

        admin_msg = (
            f"🛠️ <b>অ্যাডমিন কন্ট্রোল প্যানেল</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>মোট অ্যাক্টিভ ইউজার:</b> <code>{len(BOT_USERS)}</code> জন\n"
            f"📊 <b>মোট আপলোড ফাইল:</b> <code>{TOTAL_UPLOADS}</code> টি\n\n"
            f"📢 <b>ব্রডকাস্ট দিতে টাইপ করুন:</b>\n"
            f"<code>/broadcast আপনার মেসেজ</code>"
        )
        await query.message.reply_text(admin_msg, parse_mode="HTML")


# ---------------- MAIN APP LOOP ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_ha
