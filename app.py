import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update

from trading.master_engine import execute_trade
from bot import build_app

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL not set")


# ---------------- FLASK ----------------
app = Flask(__name__)


# ---------------- TELEGRAM ----------------
telegram_app = build_app()


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)

        update = Update.de_json(data, telegram_app.bot)

        # FIX: async-safe execution
        asyncio.run(telegram_app.process_update(update))

        return "ok"

    except Exception as e:
        print("Webhook error:", e)
        return "error", 500


# ---------------- SET WEBHOOK ----------------
@app.route("/setwebhook")
def set_webhook():
    url = f"{WEBHOOK_URL}/webhook"

    telegram_app.bot.set_webhook(url=url)

    return jsonify({
        "status": "webhook set",
        "url": url
    })


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Copy Trading System Active 🚀"


# ---------------- TRADE API ----------------
@app.route("/trade", methods=["POST"])
def trade():
    data = request.json

    result = execute_trade(
        data["symbol"],
        data["side"],
        data["entry"],
        data["sl"],
        data["tp"]
    )

    return jsonify(result)


# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Starting server on port", port)
    app.run(host="0.0.0.0", port=port)
