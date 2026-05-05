import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("trades.db", check_same_thread=False)
cur = conn.cursor()

# Trades table
cur.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    side TEXT,
    entry REAL,
    sl REAL,
    tp REAL,
    status TEXT
)
""")

# Access codes table
cur.execute("""
CREATE TABLE IF NOT EXISTS access_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    expiry_date TEXT
)
""")

conn.commit()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template_string("""
    <h1>🚀 PESAMATRIX SYSTEM</h1>
    <p>Status: Running</p>

    <form action="/trade" method="post">
        <input name="symbol" placeholder="Symbol (BTCUSDT)" required><br><br>
        <input name="side" placeholder="BUY / SELL" required><br><br>
        <input name="entry" placeholder="Entry Price" required><br><br>
        <input name="sl" placeholder="Stop Loss" required><br><br>
        <input name="tp" placeholder="Take Profit" required><br><br>

        <button type="submit">Execute Trade</button>
    </form>

    <br>
    <a href="/access">Subscriber Access</a>
    """)

# ---------------- TRADE LOGIC ----------------
def execute_trade(symbol, side, entry, sl, tp):
    return {
        "symbol": symbol,
        "side": side,
        "entry": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "status": "executed"
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

    # SAVE TRADE
    cur.execute(
        "INSERT INTO trades (symbol, side, entry, sl, tp, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            result["symbol"],
            result["side"],
            result["entry"],
            result["sl"],
            result["tp"],
            result["status"]
        )
    )
    conn.commit()

    return jsonify(result)

# ---------------- ACCESS PAGE ----------------
@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        result = cur.fetchone()

        if result:
            expiry = datetime.fromisoformat(result[2])

            if datetime.now() < expiry:
                session["access"] = True
                return redirect("/signals")

        return "Invalid or expired code ❌"

    return render_template_string("""
        <h2>Enter Access Code</h2>
        <form method="post">
            <input name="code" placeholder="Enter code" required>
            <button type="submit">Access</button>
        </form>
    """)

# ---------------- SIGNALS (PROTECTED) ----------------
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()

    return jsonify(rows)

# ---------------- GENERATE CODE (ADMIN) ----------------
@app.route("/generate")
def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute(
        "INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
        (code, expiry.isoformat())
    )
    conn.commit()

    return f"New Code: {code} (valid 24hrs)"

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Server running on port", port)
    app.run(host="0.0.0.0", port=port)
