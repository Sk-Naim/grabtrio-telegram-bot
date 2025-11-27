import os
import yt_dlp
import telebot
from telebot import types

# =============== CONFIG ===============
Token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(Token)

# Store last URL per user
user_last_url = {}
# ======================================


# ---------- MAIN MENU ----------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📥 How to use", "ℹ️ About bot")
    return kb


# ---------- /start ----------
@bot.message_handler(commands=['start'])
def start_handler(message):
    text = (
        "👋 *Welcome to GrabTrio Video Downloader!*\n\n"
        "🚀 I can instantly download videos from:\n"
        "• YouTube (Videos, Shorts — even age-restricted!)\n"
        "• Instagram (Reels, Posts)\n"
        "• Facebook (Reels, Videos)\n\n"
        "Just send any video link and choose the quality.\n\n"
        "👨‍💻 *Developer*: Sk Naimuddin"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode="Markdown")


# ---------- HOW TO USE ----------
@bot.message_handler(func=lambda m: m.text == "📥 How to use")
def how_to_use(message):
    text = (
        "📥 *How to use GrabTrio Bot*\n\n"
        "1️⃣ Copy any public video link from YouTube / Instagram / Facebook.\n"
        "2️⃣ Paste the link here and send.\n"
        "3️⃣ Choose the quality (Best / 720p / 1080p).\n"
        "4️⃣ Wait for the bot to send the video.\n\n"
        "⚠ Note: Very large 1080p videos may exceed Telegram’s upload limit."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())


# ---------- ABOUT BOT ----------
@bot.message_handler(func=lambda m: m.text == "ℹ️ About bot")
def about_bot(message):
    text = (
        "ℹ️ *GrabTrio Bot*\n"
        "Powerful video downloader bot created by *Sk Naimuddin*.\n\n"
        "Built using:\n"
        "• Python\n"
        "• yt-dlp\n"
        "• Telegram Bot API\n"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())


# ---------- URL handler ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith("http"))
def url_handler(message):
    url = message.text.strip()
    user_last_url[message.from_user.id] = url

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("⭐ Best", callback_data="q_best"),
        types.InlineKeyboardButton("720p", callback_data="q_720"),
        types.InlineKeyboardButton("1080p", callback_data="q_1080")
    )

    bot.send_message(
        message.chat.id,
        "🔗 Link received!\nSelect your preferred quality:",
        reply_markup=kb
    )


# ---------- QUALITY BUTTON HANDLER ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("q_"))
def quality_callback(call):
    user_id = call.from_user.id
    url = user_last_url.get(user_id)

    if not url:
        bot.answer_callback_query(call.id, "No URL found. Send the link again.")
        return

    q = call.data

    if q == "q_best":
        quality_label = "Best"
        fmt = "bv*+ba/b"
    elif q == "q_720":
        quality_label = "720p"
        fmt = "bv*[height<=720]+ba/b[height<=720]"
    else:
        quality_label = "1080p"
        fmt = "bv*[height<=1080]+ba/b[height<=1080]"

    bot.answer_callback_query(call.id, f"Downloading {quality_label}…")
    download_with_ytdlp(call.message.chat.id, url, fmt, quality_label)


# ---------- UNIVERSAL DOWNLOADER ----------
def download_with_ytdlp(chat_id, url, format_str, quality_label):
    status = bot.send_message(chat_id, f"⬇️ Downloading video ({quality_label})…")

    filename = "video_download.mp4"
    cookies_path = "cookies.txt"   # <--- You added this file in your repo

    ydl_opts = {
        "outtmpl": filename,
        "format": format_str,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "cookiefile": cookies_path,     # <--- FIX FOR AGE-RESTRICTED / VERIFIED VIDEOS
        "quiet": True,
        "nocheckcertificate": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Send video to Telegram
        with open(filename, "rb") as f:
            bot.send_video(chat_id, f)

        bot.edit_message_text(
            "✅ *Download complete!*\n🙏 Thanks for using *GrabTrio Bot*!",
            chat_id,
            status.message_id,
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Download error:\n`{e}`",
            chat_id,
            status.message_id,
            parse_mode="Markdown"
        )

    finally:
        if os.path.exists(filename):
            os.remove(filename)


# ---------- FALLBACK ----------
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "❌ Unsupported input.\n\nPlease send a valid video URL.",
        reply_markup=main_menu()
    )


# ---------- Run bot ----------
if __name__ == "__main__":
    print("🤖 GrabTrio Bot is running...")
    bot.polling(none_stop=True, interval=0)
