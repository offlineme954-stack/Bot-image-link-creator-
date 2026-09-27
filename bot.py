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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Config Credentials
# IMPORTANT: Replace these values with your own credentials before deployment.
BOT_TOKEN = "8649227717:AAEj9lgvTmu87PRP8gStEPkrx0ZZODbPifs"
ADMIN_CHAT_ID = "8402780798"
REQUIRED_CHANNEL = "@atiqul_services_bot"

# Global Memory Storage
USER_COOLDOWN = {}
CAPTCHA_SOLVED = set()
CAPTCHA_DATA = {}
BOT_USERS = set()
TOTAL_UPLOADS = 0
RECENT_UPLOADS = []


# ---------------- DIRECT IMAGE API HANDLERS ---------------- #

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
                if isinstance(json_data, list) and json_data and "src" in json_data[0]:
                    return "https://telegra.ph" + json_data[0]["src"]
    except Exception:
        pass
    return None


async def upload_freeimage(session: aiohttp.ClientSession, file_bytes: bytes) -> Optional[str]:
    try:
        data = aiohttp.FormData()
        data.add_field("key", "REPLACE_WITH_FREEIMAGE_API_KEY")
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
        data.add_field("key", "REPLACE_WITH_IMGBB_API_KEY")
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
        data.add_field("api_key", "REPLACE_WITH_IMGHIPPO_API_KEY")
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
        async with session.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data=data,
            timeout=7,
        ) as res:
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
    """Concurrent engine calling all configured upload APIs."""
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
            upload_tmpfiles(session, file_bytes),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, str) and result.startswith("http"):
                return result
    return None


# ---------------- UTILITY FUNCTIONS ---------------- #

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL,
            user_id=user_id,
        )
        return member.status in ["creator", "administrator", "member"]
    except Exception as exc:
        logger.error("Subscription check error: %s", exc)
        # Fail closed instead of allowing access when the check fails.
        return False


def generate_captcha(user_id: int):
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    answer = num1 + num2
    CAPTCHA_DATA[user_id] = answer
    return num1, num2, answer


def build_captcha_keyboard(answer: int) -> InlineKeyboardMarkup:
    options = [answer, answer + 1, answer - 1, answer + 2]
    random.shuffle(options)
    buttons = [
        InlineKeyboardButton(str(option), callback_data=f"captcha_val|{option}")
        for option in options
    ]
    return InlineKeyboardMarkup([buttons])


# ---------------- COMMAND HANDLERS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    BOT_USERS.add(user.id)

    # 1. Human Verification
    if user.id not in CAPTCHA_SOLVED and str(user.id) != ADMIN_CHAT_ID:
        num1, num2, answer = generate_captcha(user.id)
        await update.message.reply_text(
            f"🛡️ <b>হিউম্যান ভেরিফিকেশন:</b>\n\n"
            f"আপনি যে একজন মানুষ তা নিশ্চিত করতে নিচের হিসাবটির সঠিক উত্তরে ক্লিক করুন:\n\n"
            f"❓ <b>{num1} + {num2} = কত?</b>",
            parse_mode="HTML",
            reply_markup=build_captcha_keyboard(answer),
        )
        return

    # 2. Force Subscribe
    is_subbed = await check_subscription(user.id, context)
    if not is_subbed:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Join Official Channel",
                    url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}",
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Verified / Joined",
                    callback_data="check_sub_again",
                )
            ],
        ]
        await update.message.reply_text(
            f"⚠️ <b>বটটি ব্যবহার করতে চ্যানেল জয়েন করুন!</b>\n\n"
            f"আমাদের চ্যানেল <b>{REQUIRED_CHANNEL}</b>-এ জয়েন করে "
            f"'Verified / Joined' বাটনে চাপ দিন।",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    welcome_text = (
        f"👑 <b>স্বাগতম, {user.first_name}!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <b>Atikul Ultra Direct Image CDN Bot</b>\n\n"
        "📸 <b>যেকোনো ছবি এখনই সেন্ড করুন!</b>\n"
        "ওয়েবসাইট ও নিউজ কার্ডে ব্যবহারযোগ্য সরাসরি ছবি লিঙ্ক পেয়ে যাবেন।\n\n"
        "⚡ <i>একাধিক হাই-স্পিড আপলোড সার্ভার যুক্ত করা আছে!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📘 ব্যবহার করার নিয়ম",
                callback_data="btn_instructions",
            )
        ],
        [
            InlineKeyboardButton(
                "📢 চ্যানেল",
                url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}",
            ),
            InlineKeyboardButton(
                "👨‍💻 অ্যাডমিন",
                url=f"tg://user?id={ADMIN_CHAT_ID}",
            ),
        ],
    ]

    if str(user.id) == ADMIN_CHAT_ID:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🛠️ Admin Panel & Broadcast",
                    callback_data="open_admin_panel",
                )
            ]
        )

    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- PHOTO PROCESSOR ---------------- #

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_UPLOADS, RECENT_UPLOADS

    message = update.message
    if not message or not message.from_user:
        return

    user_id = message.from_user.id
    BOT_USERS.add(user_id)

    if user_id not in CAPTCHA_SOLVED and str(user_id) != ADMIN_CHAT_ID:
        await message.reply_text(
            "⚠️ <b>অনুগ্রহ করে আগে /start দিয়ে ভেরিফিকেশন সম্পন্ন করুন!</b>",
            parse_mode="HTML",
        )
        return

    is_subbed = await check_subscription(user_id, context)
    if not is_subbed:
        await message.reply_text(
            "⚠️ <b>চ্যানেলে জয়েন করে /start দিন!</b>",
            parse_mode="HTML",
        )
        return

    current_time = time.time()
    if (
        user_id in USER_COOLDOWN
        and current_time - USER_COOLDOWN[user_id] < 2
    ):
        await message.reply_text(
            "⚠️ <b>অপেক্ষা করুন! ১-২ সেকেন্ড পর আবার চেষ্টা করুন।</b>",
            parse_mode="HTML",
        )
        return
    USER_COOLDOWN[user_id] = current_time

    if message.photo:
        photo_obj = message.photo[-1]
        photo_file = await photo_obj.get_file()
        file_size_kb = (
            round(photo_obj.file_size / 1024, 2)
            if photo_obj.file_size
            else 0
        )
    elif (
        message.document
        and message.document.mime_type
        and message.document.mime_type.startswith("image/")
    ):
        photo_file = await message.document.get_file()
        file_size_kb = (
            round(message.document.file_size / 1024, 2)
            if message.document.file_size
            else 0
        )
    else:
        await message.reply_text(
            "❌ <b>অনুগ্রহ করে একটি ছবি ফাইল পাঠান!</b>",
            parse_mode="HTML",
        )
        return

    status_msg = await message.reply_text(
        "🔄 <i>ইমেজ প্রসেসিং শুরু হচ্ছে...</i>",
        parse_mode="HTML",
    )

    animations = [
        "⏳ <b>[■□□□□□□□□□] 10%</b> - ফাইল রিড করা হচ্ছে...",
        "⚡ <b>[███□□□□□□□] 35%</b> - আপলোড সার্ভার কানেক্ট হচ্ছে...",
        "🚀 <b>[███████□□□] 75%</b> - ডাইরেক্ট লিঙ্ক তৈরি হচ্ছে...",
        "✨ <b>[██████████] 100%</b> - আপলোড সম্পন্ন!",
    ]

    for animation in animations[:2]:
        await asyncio.sleep(0.3)
        try:
            await status_msg.edit_text(animation, parse_mode="HTML")
        except Exception:
            pass

    file_bytes = await photo_file.download_as_bytearray()

    try:
        await status_msg.edit_text(animations[2], parse_mode="HTML")
    except Exception:
        pass

    direct_link = await upload_image_multi_api(bytes(file_bytes))

    if direct_link:
        TOTAL_UPLOADS += 1
        user_info = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else message.from_user.first_name
        )

        RECENT_UPLOADS.insert(
            0,
            {
                "user": user_info,
                "user_id": user_id,
                "link": direct_link,
                "size": file_size_kb,
            },
        )
        if len(RECENT_UPLOADS) > 20:
            RECENT_UPLOADS.pop()

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔗 ডাইরেক্ট ছবি লিঙ্ক দেখুন",
                    callback_data=f"get_link|{direct_link}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🌐 ব্রাউজারে ওপেন করুন",
                    url=direct_link,
                )
            ],
        ]

        await status_msg.edit_text(
            f"🎉 <b>আপনার ডাইরেক্ট ইমেজ লিঙ্ক তৈরি হয়েছে!</b>\n\n"
            f"<code>{direct_link}</code>\n\n"
            f"🌐 <i>লিঙ্কটি কপি করে ওয়েবসাইট বা নিউজ কার্ডে ব্যবহার করতে পারেন।</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        try:
            await message.delete()
        except Exception:
            pass
    else:
        await status_msg.edit_text(
            "❌ <b>আপলোড ব্যর্থ হয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।</b>",
            parse_mode="HTML",
        )


# ---------------- ADMIN BROADCAST ---------------- #

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ <b>ব্যবহার:</b>\n<code>/broadcast আপনার মেসেজ</code>",
            parse_mode="HTML",
        )
        return

    msg = " ".join(context.args)
    count = 0

    await update.message.reply_text(
        "📢 <b>ব্রডকাস্ট শুরু হচ্ছে...</b>",
        parse_mode="HTML",
    )

    for user_id in list(BOT_USERS):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>অ্যাডমিন নোটিশ:</b>\n\n{msg}",
                parse_mode="HTML",
            )
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(
        f"✅ <b>সফলভাবে {count} জন ইউজারের কাছে মেসেজ পাঠানো হয়েছে!</b>",
        parse_mode="HTML",
    )


# ---------------- BUTTON HANDLERS ---------------- #

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    user_id = query.from_user.id
    data = query.data.split("|", 1)
    action = data[0]

    # Captcha
    if action == "captcha_val":
        if len(data) != 2:
            await query.answer("❌ অবৈধ অনুরোধ!", show_alert=True)
            return

        try:
            value = int(data[1])
        except ValueError:
            await query.answer("❌ অবৈধ উত্তর!", show_alert=True)
            return

        if CAPTCHA_DATA.get(user_id) == value:
            CAPTCHA_SOLVED.add(user_id)
            CAPTCHA_DATA.pop(user_id, None)
            await query.answer(
                "✅ আপনার উত্তর সঠিক হয়েছে!",
                show_alert=True,
            )
            try:
                await query.message.delete()
            except Exception:
                pass
            await start(update, context)
        else:
            await query.answer(
                "❌ ভুল উত্তর! আবার চেষ্টা করুন।",
                show_alert=True,
            )
            num1, num2, answer = generate_captcha(user_id)
            await query.message.edit_text(
                f"🛡️ <b>ভুল উত্তর দিয়েছেন! আবার চেষ্টা করুন:</b>\n\n"
                f"❓ <b>{num1} + {num2} = কত?</b>",
                parse_mode="HTML",
                reply_markup=build_captcha_keyboard(answer),
            )

    # Subscription re-check
    elif action == "check_sub_again":
        is_subbed = await check_subscription(user_id, context)
        if is_subbed:
            await query.answer(
                "✅ চ্যানেলে জয়েন সফল হয়েছে!",
                show_alert=True,
            )
            try:
                await query.message.delete()
            except Exception:
                pass
            await start(update, context)
        else:
            await query.answer(
                "❌ আপনি এখনো জয়েন করেননি!",
                show_alert=True,
            )

    # Instructions
    elif action == "btn_instructions":
        await query.answer()
        await query.message.reply_text(
            "📸 <b>ব্যবহারের নিয়ম:</b>\n\n"
            "১. প্রথমে /start দিন।\n"
            "২. Human Verification সম্পন্ন করুন।\n"
            "৩. প্রয়োজন হলে Official Channel-এ Join করুন।\n"
            "৪. এরপর যেকোনো ছবি পাঠান।\n"
            "৫. বট ডাইরেক্ট ইমেজ লিঙ্ক দেওয়ার চেষ্টা করবে।",
            parse_mode="HTML",
        )

    # Get link
    elif action == "get_link":
        if len(data) != 2:
            await query.answer("❌ লিঙ্ক পাওয়া যায়নি!", show_alert=True)
            return

        link = data[1]
        await query.answer("✅ লিঙ্ক প্রস্তুত!", show_alert=False)
        await query.message.reply_text(
            f"🔗 <b>আপনার লিঙ্ক:</b>\n\n<code>{link}</code>",
            parse_mode="HTML",
        )

    # Admin panel
    elif action == "open_admin_panel":
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer(
                "❌ আপনি অ্যাডমিন নন!",
                show_alert=True,
            )
            return

        admin_msg = (
            "🛠️ <b>অ্যাডমিন কন্ট্রোল প্যানেল</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>মোট অ্যাক্টিভ ইউজার:</b> <code>{len(BOT_USERS)}</code> জন\n"
            f"📊 <b>মোট আপলোড ফাইল:</b> <code>{TOTAL_UPLOADS}</code> টি\n\n"
            "📢 <b>ব্রডকাস্ট:</b>\n"
            "<code>/broadcast আপনার মেসেজ</code>"
        )
        await query.message.reply_text(
            admin_msg,
            parse_mode="HTML",
        )


# ---------------- ERROR HANDLER ---------------- #

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(
        "Unhandled exception while processing update",
        exc_info=context.error,
    )


# ---------------- MAIN APP ---------------- #

def main():
    if BOT_TOKEN == "REPLACE_WITH_YOUR_BOT_TOKEN":
        raise RuntimeError(
            "BOT_TOKEN সেট করুন। ফাইলে REPLACE_WITH_YOUR_BOT_TOKEN পরিবর্তন করুন।"
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(button_click))

    # Photos sent normally
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Images sent as document/file
    app.add_handler(
        MessageHandler(
            filters.Document.IMAGE,
            handle_photo,
        )
    )

    app.add_error_handler(error_handler)

    logger.info("Bot is starting...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
