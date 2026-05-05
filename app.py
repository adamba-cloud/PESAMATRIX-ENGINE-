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


# ---------------- SINGLE DASHBOARD ----------------
@app.route("/")
def dashboard():
    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 5")
    trades = cur.fetchall()

    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 3")
    posts = cur.fetchall()

    cur.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 5")
    notes = cur.fetchall()

    return render_template_string("""
    <html>
    <head>
        <title>PESAMATRIX DASHBOARD</title>
        <style>
            body {
                margin:0;
                font-family: Arial;
                background:#0f172a;
                color:white;
            }

            .sidebar {
                width:220px;
                height:100vh;
                background:#111827;
                position:fixed;
                padding:20px;
            }

            .sidebar a {
                display:block;
                color:#38bdf8;
                margin:12px 0;
                text-decoration:none;
            }

            .main {
                margin-left:240px;
                padding:20px;
            }

            .card {
                background:#1e293b;
                padding:15px;
                border-radius:10px;
                margin-bottom:15px;
            }

            input, button {
                width:100%;
                padding:10px;
                margin-top:8px;
                border-radius:6px;
                border:none;
            }

            button {
                background:#22c55e;
                color:white;
                cursor:pointer;
            }

            .grid {
                display:grid;
                grid-template-columns:1fr 1fr;
                gap:15px;
            }

            .box {
                background:#1e293b;
                padding:10px;
                border-radius:8px;
                margin-top:10px;
            }
        </style>
    </head>

    <body>

    <div class="sidebar">
        <h3>🚀 PESAMATRIX</h3>
        <a href="/">Dashboard</a>
        <a href="#trade">Send Signal</a>
        <a href="#posts">Posts</a>
        <a href="#notifications">Notifications</a>
        <a href="/access">Access Page</a>
        <a href="/generate">Generate Code</a>
    </div>

    <div class="main">

        <h1>📊 Admin Dashboard</h1>

        <!-- TRADE -->
        <div class="card" id="trade">
            <h3>Send Trade Signal</h3>
            <form action="/trade" method="post">
                <input name="symbol" placeholder="Symbol" required>
                <input name="side" placeholder="BUY / SELL" required>
                <input name="entry" placeholder="Entry" required>
                <input name="sl" placeholder="SL" required>
                <input name="tp" placeholder="TP" required>
                <button>Send Signal</button>
            </form>
        </div>

        <!-- POSTS -->
        <div class="card" id="posts">
            <h3>Create Post (News / Image / Video)</h3>
            <form action="/post" method="post">
                <input name="title" placeholder="Title" required>
                <input name="content" placeholder="Content" required>
                <input name="media_url" placeholder="Image/Video URL">
                <button>Post</button>
            </form>

            <h4>Recent Posts</h4>
            {% for p in posts %}
                <div class="box">
                    <b>{{p[1]}}</b>
                    <p>{{p[2]}}</p>
                </div>
            {% endfor %}
        </div>

        <!-- SIGNALS -->
        <div class="card">
            <h3>Recent Trades</h3>
            {% for t in trades %}
                <div class="box">
                    {{t[1]}} - {{t[2]}} @ {{t[3]}}
                </div>
            {% endfor %}
        </div>

        <!-- NOTIFICATIONS -->
        <div class="card" id="notifications">
            <h3>Notifications</h3>
            {% for n in notes %}
                <div class="box">
                    {{n[1]}} <br>
                    <small>{{n[2]}}</small>
                </div>
            {% endfor %}
        </div>

    </div>

    </body>
    </html>
    """, trades=trades, posts=posts, notes=notes)


# ---------------- TRADE ----------------
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
    cur.execute("INSERT INTO notifications (message, created_at) VALUES (?, ?)",
                (message, datetime.now().isoformat()))

    conn.commit()
    return redirect("/")


# ---------------- POSTS ----------------
@app.route("/post", methods=["POST"])
def post():
    title = request.form["title"]
    content = request.form["content"]
    media = request.form.get("media_url", "")

    cur.execute("INSERT INTO posts (title, content, media_url, created_at) VALUES (?, ?, ?, ?)",
                (title, content, media, datetime.now().isoformat()))

    conn.commit()
    return redirect("/")


# ---------------- ACCESS ----------------
@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        result = cur.fetchone()

        if result and datetime.now() < datetime.fromisoformat(result[2]):
            session["access"] = True
            return redirect("/")

        return "Invalid code"

    return "<h2>Enter Access Code</h2><form method='post'><input name='code'><button>Enter</button></form>"


# ---------------- GENERATE CODE ----------------
@app.route("/generate")
def generate():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute("INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
                (code, expiry.isoformat()))
    conn.commit()

    return f"CODE: {code} (24h)"


# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
