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

# ================= COMMON FOOTER =================
def footer(user=None):
    account = user["account_code"] if user else "Your Account Code"
    return f"""
    <div style="padding:15px;margin:10px;background:{CARD};border-radius:12px">
        <h3 style="color:{ACCENT}">Contacts</h3>
        📞 <a href="tel:+254781585319" style="color:{ACCENT}">+254781585319</a><br>
        📞 <a href="tel:+254717434943" style="color:{ACCENT}">+254717434943</a><br>
        🎵 <a href="https://tiktok.com/@smartgoldsignals" style="color:{ACCENT}">TikTok</a>
    </div>

    <div style="padding:15px;margin:10px;background:{CARD};border-radius:12px">
        <h3 style="color:{ACCENT}">Payments</h3>
        💳 Lipa Na Mpesa<br>
        🏦 Paybill: <b>322372</b><br>
        🔢 Account: <b>{account}</b>
    </div>
    """

# ================= HOME =================
@app.route("/")
def home():
    logo_html = f'<img src="/{LOGO_PATH}" width="140">' if os.path.exists(LOGO_PATH) else "<h2>PESAMATRIX</h2>"

    return f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <div style="text-align:center;padding:20px">
        {logo_html}
    </div>

    <div style="display:flex;justify-content:space-between;padding:15px;background:#0f172a">
        <div></div>
        <a href="/login" style="color:{ACCENT}">Admin</a>
    </div>

    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:15px">

        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/videos">🎥 Free Videos</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/news">📰 Trading News</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/access">🔐 Premium Signals</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/posts">📊 Latest Posts</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/register">🟢 Join</a></div>
        <div style="background:{CARD};padding:18px;border-radius:12px"><a href="/dashboard">👤 Dashboard</a></div>

    </div>

    {footer()}

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

        return f"""
        <body style="background:{BG};color:white">
        <h2>JOIN SUCCESS</h2>
        <h1 style="color:{ACCENT}">{code}</h1>
        <p>Free Trial: 4 Days</p>
        <a href="/user_login">Login</a>
        </body>
        """

    return f"""
    <body style="background:{BG};color:white">
    <form method='post'>
        <input name='name'><br><br>
        <input name='contact'><br><br>
        <button>Join</button>
    </form>
    </body>
    """

# ================= USER LOGIN =================
@app.route("/user_login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        code = request.form["code"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE account_code=?", (code,))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)
            return redirect("/dashboard")

        return "Invalid"

    return f"""
    <body style="background:{BG};color:white">
    <form method='post'>
        <input name='code' placeholder='Account Code'>
        <button>Login</button>
    </form>
    </body>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]

    return f"""
    <body style="background:{BG};color:white">
    <h1 style="color:{ACCENT}">Dashboard</h1>

    <div style="background:{CARD};padding:15px">
    Name: {user['name']}<br>
    Code: {user['account_code']}
    </div>

    <a href="/access">Signals</a><br>
    <a href="/mpesa">Pay</a>

    {footer(user)}

    </body>
    """

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h1>Signals</h1>"
    for r in rows:
        out += f"""
        <div style='background:{CARD};padding:10px;margin:10px'>
        {r['symbol']} | TP:{r['tp']} | {r['status']}
        </div>
        """
    return out + "</body>"

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h1>Videos</h1>"
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

    out = f"<body style='background:{BG};color:white'><h1>News</h1>"
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

    out = f"<body style='background:{BG};color:white'><h1>Posts</h1>"
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
    <h1>ADMIN</h1>

    <a href="/create_trade">Create Signal</a><br>
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
    account = user["account_code"] if user else "Your Code"

    return f"""
    <body style="background:{BG};color:white">
    <h2>Mpesa Payment</h2>

    Paybill: 322372<br>
    Account: {account}<br><br>

    After payment contact admin
    </body>
    """

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
