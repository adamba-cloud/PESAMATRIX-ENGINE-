import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL missing")


# ---------------- FLASK APP ----------------
app = Flask(__name__)


# ---------------- TELEGRAM APP ----------------
tg_app = Application.builder().token(BOT_TOKEN).build()


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working 🚀")


tg_app.add_handler(CommandHandler("start", start))


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)

        update = Update.de_json(data, tg_app.bot)

        asyncio.run(tg_app.process_update(update))

        return "ok"

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "error", 500


# ---------------- SET WEBHOOK ----------------
@app.route("/setwebhook")
def set_webhook():
    url = f"{WEBHOOK_URL}/webhook"

    tg_app.bot.set_webhook(url=url)

    return {
        "status": "webhook set",
        "url": url
    }


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "System Running 🚀"


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Starting server on port", port)

    app.run(host="0.0.0.0", port=port)
