import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# إعداد السجلات (Logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ⚠️ ضع التوكن الخاص ببوتك هنا
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# مجلد التنزيل المؤقت
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحباً بك!\n"
        "أرسل لي رابط فيديو من (YouTube, TikTok, Facebook, Instagram) "
        "وسأقوم بتحميله بأعلى جودة وبأقصى سرعة ممكنة! 🚀"
    )

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    status_msg = await update.message.reply_text("⚡ جاري معالجة الرابط وتحميل الفيديو بأعلى جودة...")

    # خيارات yt-dlp للسرعة العالية والجودة الخارقة
    ydl_opts = {
        # اختيار أعلى جودة فيديو + أعلى جودة صوت والدمج بينهما
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        # خيارات زيادة السرعة
        'concurrent_fragment_downloads': 10,  # تحميل 10 أجزاء في نفس الوقت لسرعة خيالية
        'buffersize': 1024 * 1024,             # حجم البوفر 1 ميجابايت للتحميل السريع
    }

    loop = asyncio.get_running_loop()
    file_path = None

    try:
        # تشغيل التنزيل في خيط منفصل لتجنب إيقاف البوت (Non-blocking)
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await loop.run_in_executor(None, download)

        # تعديل الامتداد في حال تم دمج الفيديو إلى mp4
        if not os.path.exists(file_path):
            base_path = os.path.splitext(file_path)[0]
            if os.path.exists(f"{base_path}.mp4"):
                file_path = f"{base_path}.mp4"

        await status_msg.edit_text("📤 جاري إرسال الفيديو إليك...")

        # إرسال الفيديو إلى المستخدم
        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ تم التحميل بأعلى جودة وسرعة!",
                supports_streaming=True
            )

        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        await status_msg.edit_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")

    finally:
        # مسح الملف من السيرفر بعد الإرسال لتوفير المساحة
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))

    print("🚀 البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
