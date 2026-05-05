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

cur.execute("""
CREATE TABLE IF NOT EXISTS access_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    expiry_date TEXT
)
""")

conn.commit()

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

# ---------------- HOME (ADMIN DASHBOARD) ----------------
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>PESAMATRIX</title>
        <style>
            body { font-family: Arial; background:#0f172a; color:white; text-align:center; }
            .card { background:#1e293b; padding:20px; margin:20px auto; width:350px; border-radius:10px; }
            input { width:100%; padding:10px; margin:5px 0; }
            button { width:100%; padding:10px; background:#22c55e; color:white; border:none; cursor:pointer; }
            a { color:#38bdf8; }
        </style>
    </head>
    <body>

        <h1>🚀 PESAMATRIX ADMIN PANEL</h1>

        <div class="card">
            <h3>Create Signal</h3>

            <form action="/trade" method="post">
                <input name="symbol" placeholder="Symbol (EURUSD)" required>
                <input name="side" placeholder="BUY / SELL" required>
                <input name="entry" placeholder="Entry Price" required>
                <input name="sl" placeholder="Stop Loss" required>
                <input name="tp" placeholder="Take Profit" required>

                <button type="submit">SEND SIGNAL</button>
            </form>
        </div>

        <a href="/signals">📊 View Live Signals</a><br>
        <a href="/access">🔐 Subscriber Access</a><br>
        <a href="/generate">🧾 Generate Access Code</a>

    </body>
    </html>
    """)

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

# ---------------- SIGNALS (SUBSCRIBER DASHBOARD) ----------------
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()

    html = """
    <html>
    <head>
        <title>Signals</title>
        <style>
            body { font-family: Arial; background:#0f172a; color:white; text-align:center; }
            .box {
                background:#1e293b;
                margin:15px auto;
                padding:15px;
                width:300px;
                border-radius:10px;
                box-shadow:0 0 10px #000;
            }
            .buy { color:#22c55e; font-weight:bold; }
            .sell { color:#ef4444; font-weight:bold; }
        </style>
    </head>
    <body>

        <h1>📊 LIVE SIGNALS</h1>
    """

    for r in rows:
        color = "buy" if r[2] == "BUY" else "sell"

        html += f"""
        <div class="box">
            <h3>{r[1]}</h3>
            <p class="{color}">{r[2]}</p>
            <p>Entry: {r[3]}</p>
            <p>SL: {r[4]}</p>
            <p>TP: {r[5]}</p>
            <p>Status: {r[6]}</p>
        </div>
        """

    html += "</body></html>"
    return render_template_string(html)

# ---------------- GENERATE ACCESS CODE ----------------
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
