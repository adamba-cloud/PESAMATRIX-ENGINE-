import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template_string("""
    <h1>🚀 PESAMATRIX SYSTEM</h1>
    <p>Status: Running</p>

    <form action="/trade" method="post">
        <input name="symbol" placeholder="Symbol (e.g BTCUSDT)" required><br><br>
        <input name="side" placeholder="BUY / SELL" required><br><br>
        <input name="entry" placeholder="Entry Price" required><br><br>
        <input name="sl" placeholder="Stop Loss" required><br><br>
        <input name="tp" placeholder="Take Profit" required><br><br>

        <button type="submit">Execute Trade</button>
    </form>
    """)

# ---------------- TRADE ENGINE ----------------
def execute_trade(symbol, side, entry, sl, tp):
    # SIMPLE MOCK (replace later)
    return {
        "status": "success",
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "sl": sl,
        "tp": tp
    }

# ---------------- TRADE ROUTE ----------------
@app.route("/trade", methods=["POST"])
def trade():
    data = request.form

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
    print("Server running on port", port)
    app.run(host="0.0.0.0", port=port)
