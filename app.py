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

# FOOTER (only for main pages)
def footer(user=None):
    acc = user["account_code"] if user else "Your Code"
    return f"""
    <div style="background:{CARD};padding:15px;margin:10px;border-radius:12px">
    <h3 style="color:{ACCENT}">📞 Contacts</h3>
    <a href="tel:+254781585319" style="color:{ACCENT}">+254781585319</a><br>
    <a href="tel:+254717434943" style="color:{ACCENT}">+254717434943</a><br>
    <a href="https://tiktok.com/@smartgoldsignals" style="color:{ACCENT}">TikTok</a>
    </div>

    <div style="background:{CARD};padding:15px;margin:10px;border-radius:12px">
    <h3 style="color:{ACCENT}">💳 Payments</h3>
    Paybill: 322372<br>
    Account: {acc}
    </div>
    """

# ================= HOME =================
@app.route("/")
def home():
    logo = f'<img src="/{LOGO_PATH}" width="120">' if os.path.exists(LOGO_PATH) else "<h2>PESAMATRIX</h2>"

    return f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <div style="text-align:center">{logo}</div>

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
    High accuracy trading signals in real time.
    </div>

    {footer()}

    <a href="/login" style="color:{ACCENT}">Admin</a>

    </body>
    """

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()
        trial_end = datetime.now() + timedelta(days=4)

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?)",
                    (request.form["name"], request.form["contact"], code,
                     trial_end.isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"<body style='background:{BG};color:white'>Account: {code}<br><a href='/user_login'>Login</a></body>"

    return f"<body style='background:{BG};color:white'><form method='post'><input name='name'><input name='contact'><button>Join</button></form></body>"

# ================= LOGIN =================
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

    return f"<body style='background:{BG};color:white'><form method='post'><input name='code'><button>Login</button></form></body>"

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]
    status = "ACTIVE" if datetime.now() < datetime.fromisoformat(user["trial_end"]) else "EXPIRED"

    return f"""
    <body style="background:{BG};color:white">
    <h2 style="color:{ACCENT}">User Dashboard</h2>

    Name: {user['name']}<br>
    Account: {user['account_code']}<br>
    Status: {status}<br>

    <a href="/access">Signals</a><br>
    {footer(user)}
    </body>
    """

# ================= ACCESS =================
@app.route("/access")
def access():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]

    if datetime.now() > datetime.fromisoformat(user["trial_end"]):
        return "Trial Expired"

    return redirect("/signals")

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h2 style='color:{ACCENT}'>Signals</h2>"
    for r in rows:
        out += f"<div style='background:{CARD};margin:10px;padding:10px'>{r['symbol']} | {r['status']}</div>"
    return out

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h2 style='color:{ACCENT}'>Videos</h2>"
    for r in rows:
        out += f"<video controls width='100%'><source src='/{r['media']}'></video>"
    return out

# ================= NEWS =================
@app.route("/news")
def news():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h2 style='color:{ACCENT}'>News</h2>"
    for r in rows:
        out += f"<div style='background:{CARD};margin:10px'>{r['title']}</div>"
    return out

# ================= POSTS =================
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h2 style='color:{ACCENT}'>Posts</h2>"
    for r in rows:
        out += f"<div style='background:{CARD};margin:10px'>{r['title']}</div>"
    return out

# ================= ADMIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

    return "<form method='post'><input name='password'><button>Login</button></form>"

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return f"""
    <body style="background:{BG};color:white">
    <h2 style="color:{ACCENT}">Admin Dashboard</h2>

    <a href="/create_trade">Create Signal</a><br>
    <a href="/manage_trades">Manage Trades</a><br>
    <a href="/upload">Upload Media</a><br>
    <a href="/generate_code">Generate Code</a><br>
    <a href="/users">Users</a><br>

    </body>
    """

# ================= START =================
if __name__ == "__main__":
    app.run()
