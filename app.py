import os
from flask import Flask, request, jsonify
from config import BOT_TOKEN, WEBHOOK_URL
from bot import build_app
from trading.master_engine import execute_trade

app = Flask(__name__)

# ---------------- TELEGRAM SETUP ----------------
telegram_app = build_app()


# ---------------- WEBHOOK ROUTE ----------------
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), telegram_app)
    await telegram_app.process_update(update)
    return "ok"


# ---------------- SET WEBHOOK AUTOMATICALLY ----------------
@app.route("/setwebhook")
def set_webhook():
    url = f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    telegram_app.bot.set_webhook(url=url)
    return f"Webhook set to {url}"


# ---------------- FLASK API ----------------
@app.route("/")
def home():
    return "Copy Trading System Active 🚀"


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
    app.run(host="0.0.0.0", port=port)
