import os
import time
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =====================
# CONFIG
# =====================
TOKEN = "8315801197:AAE46Oucf9srGFYUUVIuhAwPWveWzCmpf5s"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ANTI_SPAM_SECONDS = 10
last_request = {}

# =====================
# MAIN MENU
# =====================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎵 تحميل صوت (M4A)", callback_data="audio")],
        [InlineKeyboardButton("🎬 تحميل فيديو (MP4)", callback_data="video")],
        [InlineKeyboardButton("ℹ️ طريقة الاستخدام", callback_data="help")]
    ]

    text = (
        "🌙 *بوت التحميل الذكي*\n\n"
        "⬇️ يدعم جميع المنصات\n"
        "🎵 صوت M4A (بدون تحويل)\n"
        "🎬 فيديو MP4\n\n"
        "📌 اختر الصيغة ثم أرسل الرابط\n"
        "📱 مناسب للآيفون (a-Shell)"
    )

    return text, InlineKeyboardMarkup(keyboard)

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, keyboard = main_menu()
    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# =====================
# BUTTONS
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 🔙 BACK
    if query.data == "back":
        text, keyboard = main_menu()
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    # ℹ️ HELP
    if query.data == "help":
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back")]]
        await query.edit_message_text(
            "📖 *طريقة الاستخدام*\n\n"
            "1️⃣ اختر (صوت أو فيديو)\n"
            "2️⃣ أرسل رابط الفيديو\n"
            "3️⃣ استلم الملف فورًا\n\n"
            "⚡ سريع\n📱 خفيف\n🔕 حماية سبام",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # MODE
    context.user_data["mode"] = query.data
    keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back")]]
    await query.edit_message_text(
        f"✅ *تم الاختيار:* `{query.data.upper()}`\n\n📥 أرسل الرابط الآن",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# =====================
# ANTI SPAM
# =====================
def is_spam(user_id):
    now = time.time()
    if user_id in last_request and now - last_request[user_id] < ANTI_SPAM_SECONDS:
        return True
    last_request[user_id] = now
    return False

# =====================
# DOWNLOAD
# =====================
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_spam(user_id):
        await update.message.reply_text("⏳ انتظر قليلًا قبل إرسال رابط آخر")
        return

    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("⚠️ اختر الصيغة أولًا من القائمة /start")
        return

    url = update.message.text
    status = await update.message.reply_text("⏳ جاري المعالجة...")

    try:
        # 🎵 AUDIO M4A
        if mode == "audio":
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file = ydl.prepare_filename(info)

            await update.message.reply_audio(audio=open(file, 'rb'))

        # 🎬 VIDEO MP4 (720p)
        elif mode == "video":
            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file = ydl.prepare_filename(info)

            await update.message.reply_video(video=open(file, 'rb'))

        await status.delete()

    except Exception:
        await status.edit_text("❌ فشل التحميل\nتأكد من صحة الرابط")

# =====================
# RUN
# =====================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

print("Bot running (a-Shell mode)...")
app.run_polling()