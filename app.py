import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

# CONFIG
ADMIN_PASSWORD = "admin123"
UPLOAD_FOLDER = "static/uploads"
LOGO_PATH = "static/logo.png"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)

BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"
TEXT = "font-size:18px;"

# DATABASE
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT,
        account_code TEXT,
        trial_end TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        side TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        status TEXT,
        created_at TEXT,
        expiry_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        media TEXT,
        type TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        expiry TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================
@app.route("/")
def home():
    logo = f'<img src="/{LOGO_PATH}" width="120">' if os.path.exists(LOGO_PATH) else "<h2>PESAMATRIX</h2>"

    return f"""
    <body style="background:{BG};color:white;font-family:Arial;{TEXT}">
    <div style="text-align:center">{logo}</div>

    <h2 style="color:{ACCENT};text-align:center">Trading Platform</h2>

    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;padding:15px">

    <div style="background:{CARD};padding:15px"><a href="/videos" style="color:{ACCENT}">🎥 Free Videos</a></div>
    <div style="background:{CARD};padding:15px"><a href="/news" style="color:{ACCENT}">📰 Trading News</a></div>
    <div style="background:{CARD};padding:15px"><a href="/access" style="color:{ACCENT}">🔐 Premium Signals</a></div>
    <div style="background:{CARD};padding:15px"><a href="/posts" style="color:{ACCENT}">📊 Latest Posts</a></div>
    <div style="background:{CARD};padding:15px"><a href="/register" style="color:{ACCENT}">🟢 Join</a></div>
    <div style="background:{CARD};padding:15px"><a href="/dashboard" style="color:{ACCENT}">👤 Dashboard</a></div>

    </div>

    <div style="padding:10px">
    <h3 style="color:{ACCENT}">About Us</h3>
    We provide high accuracy forex trading signals in real-time with strong risk management.
    </div>

    <a href="/login" style="color:{ACCENT}">Admin</a>
    </body>
    """

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>🎥 Free Videos</h2>"

    for r in rows:
        if r["media"].startswith("http"):
            out += f"<iframe width='100%' height='200' src='{r['media']}'></iframe>"
        else:
            out += f"<video controls width='100%'><source src='/{r['media']}'></video>"

    return out + "</body>"

# ================= NEWS =================
@app.route("/news")
def news():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='news'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>📰 Trading News</h2>"

    for r in rows:
        out += f"<div style='background:{CARD};padding:10px;margin:10px'>{r['title']}<br>{r['content']}</div>"

    return out + "</body>"

# ================= POSTS =================
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='post'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>📊 Latest Posts</h2>"

    for r in rows:
        out += f"<div style='background:{CARD};padding:10px;margin:10px'>{r['title']}</div>"

    return out + "</body>"

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Live Signals</h2>"

    for r in rows:
        out += f"""
        <div style='background:{CARD};margin:10px;padding:15px;border-radius:10px'>
        <b style='color:{ACCENT}'>{r['symbol']}</b><br><br>
        Entry: {r['entry']}<br>
        TP: {r['tp']}<br>
        SL: {r['sl']}<br>
        Status: {r['status']}
        </div>
        """

    return out + "</body>"

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return f"""
    <body style="background:{BG};color:white;{TEXT}">
    <h2 style="color:{ACCENT}">Admin Dashboard</h2>

    <a href="/create_trade">Create Signal</a><br>
    <a href="/manage_trades">Manage Trades</a><br>
    <a href="/upload">Upload Media</a><br>
    <a href="/generate_code">Generate Code</a><br>
    <a href="/users">Users</a><br>
    <a href="/create_news">Create News</a><br>

    </body>
    """

# ================= MANAGE TRADES =================
@app.route("/manage_trades")
def manage_trades():
    return f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Manage Trades Working</h2></body>"

# ================= UPLOAD =================
@app.route("/upload", methods=["GET","POST"])
def upload():
    return f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Upload Media Working</h2></body>"

# ================= GENERATE CODE =================
@app.route("/generate_code")
def generate_code():
    return f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Code Generated</h2></body>"

# ================= USERS =================
@app.route("/users")
def users():
    return f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Users List</h2></body>"

# ================= CREATE NEWS =================
@app.route("/create_news")
def create_news():
    return f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Create News Page</h2></body>"

# ================= START =================
if __name__ == "__main__":
    app.run()
