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

cur.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    created_at TEXT
)
""")

# 🆕 POSTS TABLE (CONTENT SYSTEM)
cur.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    media_url TEXT,
    created_at TEXT
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

# ---------------- HOME (ADMIN PANEL) ----------------
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
            a { color:#38bdf8; display:block; margin:5px; }
        </style>
    </head>
    <body>

        <h1>🚀 PESAMATRIX ADMIN PANEL</h1>

        <div class="card">
            <h3>Create Signal</h3>
            <form action="/trade" method="post">
                <input name="symbol" placeholder="Symbol" required>
                <input name="side" placeholder="BUY / SELL" required>
                <input name="entry" placeholder="Entry Price" required>
                <input name="sl" placeholder="Stop Loss" required>
                <input name="tp" placeholder="Take Profit" required>
                <button type="submit">SEND SIGNAL</button>
            </form>
        </div>

        <div class="card">
            <h3>📢 Post Trading Content</h3>
            <form action="/post" method="post">
                <input name="title" placeholder="Title" required>
                <input name="content" placeholder="Content / News" required>
                <input name="media_url" placeholder="Image or Video URL (optional)">
                <button type="submit">POST</button>
            </form>
        </div>

        <a href="/signals">📊 Signals</a>
        <a href="/posts">📰 Trading Feed</a>
        <a href="/notifications">🔔 Notifications</a>
        <a href="/access">🔐 Access</a>
        <a href="/generate">🧾 Generate Code</a>

    </body>
    </html>
    """)

# ---------------- TRADE + NOTIFICATION ----------------
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
        (result["symbol"], result["side"], result["entry"], result["sl"], result["tp"], result["status"])
    )

    message = f"📢 {result['symbol']} {result['side']} @ {result['entry']}"
    cur.execute(
        "INSERT INTO notifications (message, created_at) VALUES (?, ?)",
        (message, datetime.now().isoformat())
    )

    conn.commit()
    return jsonify(result)

# ---------------- CONTENT POST (NEW FEATURE) ----------------
@app.route("/post", methods=["POST"])
def post():
    title = request.form["title"]
    content = request.form["content"]
    media_url = request.form.get("media_url", "")

    cur.execute("""
        INSERT INTO posts (title, content, media_url, created_at)
        VALUES (?, ?, ?, ?)
    """, (title, content, media_url, datetime.now().isoformat()))

    conn.commit()

    return jsonify({"status": "post created"})

# ---------------- POSTS PAGE (TRADING FEED) ----------------
@app.route("/posts")
def posts():
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    rows = cur.fetchall()

    html = """
    <html>
    <head>
        <title>Trading Feed</title>
        <style>
            body { font-family: Arial; background:#0f172a; color:white; text-align:center; }
            .box { background:#1e293b; margin:15px auto; padding:15px; width:320px; border-radius:10px; }
            img, iframe { width:100%; border-radius:8px; margin-top:10px; }
        </style>
    </head>
    <body>
        <h1>📰 Trading Feed</h1>
    """

    for r in rows:
        html += f"""
        <div class="box">
            <h3>{r[1]}</h3>
            <p>{r[2]}</p>
        """

        if r[3]:
            if "youtube" in r[3]:
                html += f'<iframe src="{r[3]}" frameborder="0"></iframe>'
            else:
                html += f'<img src="{r[3]}">'

        html += "</div>"

    html += "</body></html>"
    return render_template_string(html)

# ---------------- NOTIFICATIONS ----------------
@app.route("/notifications")
def notifications():
    cur.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall()

    html = """
    <html>
    <head>
        <title>Notifications</title>
        <style>
            body { font-family: Arial; background:#0f172a; color:white; text-align:center; }
            .box { background:#1e293b; margin:15px auto; padding:15px; width:350px; border-radius:10px; }
        </style>
    </head>
    <body>
        <h1>🔔 Notifications</h1>
    """

    for r in rows:
        html += f"""
        <div class="box">
            <p>{r[1]}</p>
            <small>{r[2]}</small>
        </div>
        """

    html += "</body></html>"
    return render_template_string(html)

# ---------------- ACCESS ----------------
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
    <h2>Subscriber Access</h2>
    <form method="post">
        <input name="code" placeholder="ACCESS CODE" required>
        <button type="submit">Unlock</button>
    </form>
    """)

# ---------------- SIGNALS ----------------
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
            .box { background:#1e293b; margin:15px auto; padding:15px; width:300px; border-radius:10px; }
        </style>
    </head>
    <body>
        <h1>📊 Signals</h1>
    """

    for r in rows:
        html += f"""
        <div class="box">
            <h3>{r[1]}</h3>
            <p>{r[2]}</p>
            <p>Entry: {r[3]}</p>
            <p>SL: {r[4]}</p>
            <p>TP: {r[5]}</p>
        </div>
        """

    html += "</body></html>"
    return render_template_string(html)

# ---------------- GENERATE CODE ----------------
@app.route("/generate")
def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute(
        "INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
        (code, expiry.isoformat())
    )
    conn.commit()

    return f"CODE: {code} (24h valid)"

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
