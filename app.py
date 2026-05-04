import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application

from trading.master_engine import execute_trade
from bot import build_app

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL not set")


# ---------------- FLASK APP ----------------
app = Flask(__name__)


# ---------------- TELEGRAM APP ----------------
telegram_app = build_app()
telegram_app.initialize()
telegram_app.start()


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    update = Update.de_json(data, telegram_app.bot)
    telegram_app.process_update(update)

    return "ok"


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


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
