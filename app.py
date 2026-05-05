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
TEXT = "font-size:20px;"

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
        entry REAL,
        sl REAL,
        tp REAL,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        media TEXT,
        type TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# COMMON FOOTER
def footer(user=None):
    acc = user["account_code"] if user else "Your Code"
    return f"""
    <div style="background:{CARD};padding:15px;margin:15px;border-radius:12px">
        <h3 style="color:{ACCENT}">📞 Contacts</h3>
        <a href="tel:+254781585319" style="color:{ACCENT}">+254781585319</a><br>
        <a href="tel:+254717434943" style="color:{ACCENT}">+254717434943</a><br>
        <a href="https://tiktok.com/@smartgoldsignals" style="color:{ACCENT}">TikTok</a>
    </div>

    <div style="background:{CARD};padding:15px;margin:15px;border-radius:12px">
        <h3 style="color:{ACCENT}">💳 Payments</h3>
        Lipa Na Mpesa<br>
        Paybill: <b>322372</b><br>
        Account: <b>{acc}</b>
    </div>
    """

# HOME
@app.route("/")
def home():
    logo = f'<img src="/{LOGO_PATH}" width="120">' if os.path.exists(LOGO_PATH) else "<h2>PESAMATRIX</h2>"

    return f"""
    <body style="background:{BG};color:white;font-family:Arial;{TEXT}">

    <div style="text-align:center">{logo}</div>
    <h2 style="color:{ACCENT};text-align:center">Smart Trading Platform</h2>

    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;padding:15px">

    <div style="background:{CARD};padding:15px"><a href="/videos" style="color:{ACCENT}">🎥 Free Videos</a></div>
    <div style="background:{CARD};padding:15px"><a href="/news" style="color:{ACCENT}">📰 Trading News</a></div>
    <div style="background:{CARD};padding:15px"><a href="/posts" style="color:{ACCENT}">📊 Latest Posts</a></div>
    <div style="background:{CARD};padding:15px"><a href="/access" style="color:{ACCENT}">🔐 Premium Signals</a></div>
    <div style="background:{CARD};padding:15px"><a href="/register" style="color:{ACCENT}">🟢 Join</a></div>
    <div style="background:{CARD};padding:15px"><a href="/dashboard" style="color:{ACCENT}">👤 Dashboard</a></div>

    </div>

    <div style="padding:15px">
        <h3 style="color:{ACCENT}">About Us</h3>
        We provide high accuracy forex signals, real-time updates, and professional risk management.
    </div>

    {footer()}

    <div style="text-align:center">
        <a href="/login" style="color:{ACCENT}">Admin</a>
    </div>

    </body>
    """

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()
        trial_end = datetime.now() + timedelta(days=4)

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?)",
                    (request.form["name"], request.form["phone"], code,
                     trial_end.isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"<body style='background:{BG};color:white;{TEXT}'>Account Code: <b>{code}</b><br><a href='/user_login'>Login</a></body>"

    return f"""
    <body style="background:{BG};color:white;{TEXT}">
    Name:<br><input name='name'><br><br>
    Phone:<br><input name='phone'><br><br>
    <button>Join</button>
    </body>
    """

# LOGIN
@app.route("/user_login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE account_code=?", (request.form["code"],))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)
            return redirect("/dashboard")

    return f"<body style='background:{BG};color:white;{TEXT}'>Account Code:<br><input name='code'><button>Login</button></body>"

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]
    status = "ACTIVE" if datetime.now() < datetime.fromisoformat(user["trial_end"]) else "EXPIRED"

    return f"""
    <body style="background:{BG};color:white;{TEXT}">
    <h2 style="color:{ACCENT}">User Dashboard</h2>

    Name: {user['name']}<br>
    Account: {user['account_code']}<br>
    Status: {status}<br><br>

    <a href="/access" style="color:{ACCENT}">View Signals</a>

    {footer(user)}
    </body>
    """

# PREMIUM ACCESS
@app.route("/access")
def access():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]

    if datetime.now() > datetime.fromisoformat(user["trial_end"]):
        return f"<body style='background:{BG};color:white'>🔒 Access Locked - Please Pay</body>"

    return redirect("/signals")

# SIGNALS
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
        <div style='background:{CARD};padding:15px;margin:10px;border-radius:10px'>
        <h3 style='color:{ACCENT}'>{r['symbol']}</h3>
        Entry: {r['entry']}<br>
        TP: {r['tp']}<br>
        SL: {r['sl']}<br>
        Status: {r['status']}
        </div>
        """

    return out + "</body>"

# VIDEOS
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Videos</h2>"

    for r in rows:
        out += f"<video controls width='100%'><source src='/{r['media']}'></video>"

    return out + footer() + "</body>"

# NEWS
@app.route("/news")
def news():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Trading News</h2>"

    for r in rows:
        out += f"<div style='background:{CARD};padding:10px;margin:10px'>{r['title']}</div>"

    return out + footer() + "</body>"

# POSTS
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Latest Posts</h2>"

    for r in rows:
        out += f"<div style='background:{CARD};padding:10px;margin:10px'>{r['title']}</div>"

    return out + footer() + "</body>"

# ADMIN LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

    return f"<body style='background:{BG};color:white'><input name='password'><button>Login</button></body>"

# ADMIN DASHBOARD
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
    <a href="/users">Users</a><br>
    </body>
    """

# START
if __name__ == "__main__":
    app.run()
