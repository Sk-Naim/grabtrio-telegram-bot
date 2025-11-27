import os
import telebot
from telebot import types
from flask import Flask, request
import yt_dlp

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://your-bot.onrender.com/webhook

bot = telebot.TeleBot(TOKEN, threaded=True)
server = Flask(__name__)

user_last_url = {}
# ----------------------------------------


# ---------- MAIN MENU ----------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📥 How to use", "ℹ️ About bot")
    return kb


# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start_handler(message):
    text = (
        "👋 *Welcome to GrabTrio Video Downloader!*\n\n"
        "🚀 I can instantly download videos from:\n"
        "• YouTube (Videos, Shorts)\n"
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
        "1️⃣ Copy any public video link.\n"
        "2️⃣ Paste the link here.\n"
        "3️⃣ Choose Best / 720p / 1080p.\n"
        "4️⃣ Wait for download.\n\n"
        "⚠ 1080p may exceed Telegram limits."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# ---------- ABOUT BOT ----------
@bot.message_handler(func=lambda m: m.text == "ℹ️ About bot")
def about_bot(message):
    text = (
        "ℹ️ *GrabTrio Bot*\n"
        "Created by *Sk Naimuddin*.\n"
        "Powered by Python & yt-dlp."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# ---------- URL handler ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith("http"))
def url_handler(message):
    url = message.text.strip()
    user_last_url[message.from_user.id] = url

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("⭐ Best", callback_data="q_best"),
        types.InlineKeyboardButton("720p", callback_data="q_720"),
        types.InlineKeyboardButton("1080p", callback_data="q_1080"),
    )

    bot.send_message(
        message.chat.id,
        "🔗 Link received!\nSelect your preferred quality:",
        reply_markup=kb
    )


# ---------- QUALITY SELECTION ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("q_"))
def quality_callback(call):
    user_id = call.from_user.id
    url = user_last_url.get(user_id)

    if not url:
        bot.answer_callback_query(call.id, "No URL found. Send the link again.")
        return

    q = call.data

    if q == "q_best":
        fmt = "bv*+ba/b"
        label = "Best"
    elif q == "q_720":
        fmt = "bv*[height<=720]+ba/b[height<=720]"
        label = "720p"
    else:
        fmt = "bv*[height<=1080]+ba/b[height<=1080]"
        label = "1080p"

    bot.answer_callback_query(call.id, f"Downloading {label}…")
    download_with_ytdlp(call.message.chat.id, url, fmt, label)


# ---------- DOWNLOAD FUNCTION ----------
def download_with_ytdlp(chat_id, url, fmt, label):
    status = bot.send_message(chat_id, f"⬇️ Downloading video ({label})…")

    filename = "video.mp4"
    ydl_opts = {
        "format": fmt,
        "outtmpl": filename,
        "noplaylist": True,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(filename, "rb") as f:
            bot.send_video(chat_id, f)

        bot.edit_message_text(
            "✅ Download complete!",
            chat_id,
            status.message_id
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Download error:\n`{e}`",
            chat_id,
            status.message_id,
            parse_mode="Markdown",
        )

    finally:
        if os.path.exists(filename):
            os.remove(filename)


# ---------------- FLASK WEBHOOK SERVER ----------------
@server.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Invalid request", 403


# Run locally OR via Render
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    server.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
