import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this")

# ================= CONFIG =================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_FOLDER = "static/uploads"
LOGO_PATH = "static/logo.png"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)

BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"

# ================= DATABASE =================
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

    conn.commit()
    conn.close()

init_db()

# ================= GLOBAL FOOTER =================
def footer(user=None):
    acc = user["account_code"] if user else "Your Account Code"
    return f"""
    <div style="padding:15px;margin:10px;background:{CARD};border-radius:12px">
        <h3 style="color:{ACCENT}">📞 Contacts</h3>
        <a href="tel:+254781585319" style="color:{ACCENT}">+254781585319</a><br>
        <a href="tel:+254717434943" style="color:{ACCENT}">+254717434943</a><br>
        <a href="https://tiktok.com/@smartgoldsignals" style="color:{ACCENT}">TikTok</a>
    </div>

    <div style="padding:15px;margin:10px;background:{CARD};border-radius:12px">
        <h3 style="color:{ACCENT}">💳 Payments</h3>
        Paybill: <b>322372</b><br>
        Account: <b>{acc}</b>
    </div>
    """

# ================= HOME =================
@app.route("/")
def home():
    logo = f'<img src="/{LOGO_PATH}" width="140">' if os.path.exists(LOGO_PATH) else "<h2>PESAMATRIX</h2>"

    return f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <div style="text-align:center;padding:20px">
        {logo}
    </div>

    <div style="display:flex;justify-content:space-between;padding:15px;background:#0f172a">
        <div></div>
        <a href="/login" style="color:{ACCENT}">Admin</a>
    </div>

    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:15px">

        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/videos" style="color:{ACCENT}">🎥 Free Videos</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/news" style="color:{ACCENT}">📰 Trading News</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/access" style="color:{ACCENT}">🔐 Premium Signals</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/posts" style="color:{ACCENT}">📊 Latest Posts</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/register" style="color:{ACCENT}">🟢 Join</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/dashboard" style="color:{ACCENT}">👤 Dashboard</a></div>

    </div>

    {footer()}

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

    out = f"<body style='background:{BG};color:white'><h1>🎥 Videos</h1>"
    for r in rows:
        if "http" in r["media"]:
            out += f"<iframe width='100%' height='200' src='{r['media']}'></iframe>"
        else:
            out += f"<video controls width='100%'><source src='/{r['media']}'></video>"
    return out + footer() + "</body>"

# ================= NEWS =================
@app.route("/news")
def news():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h1>📰 Trading News</h1>"
    for r in rows:
        out += f"<div style='background:{CARD};padding:10px;margin:10px'>{r['title']}</div>"
    return out + footer() + "</body>"

# ================= POSTS =================
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h1>📊 Posts</h1>"
    for r in rows:
        out += f"<div style='background:{CARD};padding:10px;margin:10px'>{r['title']}</div>"
    return out + footer() + "</body>"

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return f"""
    <body style="background:{BG};color:white">
    <h1>ADMIN DASHBOARD</h1>

    <a href="/create_trade">Create Signal</a><br>
    <a href="/manage_trades">Manage Trades</a><br>
    <a href="/upload">Upload Media</a><br>
    <a href="/upload_logo">Upload Logo</a><br>

    </body>
    """

# ================= UPLOAD LOGO =================
@app.route("/upload_logo", methods=["GET","POST"])
def upload_logo():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files["file"]
        file.save(LOGO_PATH)
        return redirect("/")

    return f"""
    <body style="background:{BG};color:white">
    <h2>Upload Logo</h2>
    <form method='post' enctype='multipart/form-data'>
    <input type='file' name='file'>
    <button>Upload</button>
    </form>
    </body>
    """

# ================= MPESA =================
@app.route("/mpesa")
def mpesa():
    user = session.get("user")
    acc = user["account_code"] if user else "Your Code"

    return f"""
    <body style="background:{BG};color:white">
    <h2>Mpesa Payment</h2>

    Paybill: 322372<br>
    Account: {acc}<br><br>

    After payment contact admin
    {footer(user)}
    </body>
    """

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
