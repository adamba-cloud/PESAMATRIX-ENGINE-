import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this")

# ================= CONFIG =================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DATABASE =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        side TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        status TEXT,
        created_at TEXT,
        expiry_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS access_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        expiry TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        media TEXT,
        type TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ================= SETTINGS =================
def get_setting(key, default=""):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = db()
    cur = conn.cursor()
    cur.execute("REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


# ================= GLOBAL THEME =================
BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"
GREEN = "#22c55e"
RED = "#ef4444"

CONTACTS = """
📞 +254 781 585 319 / +254 717 434 943<br>
📧 support@pesamatrix.com<br>
📱 Telegram | Instagram | Twitter<br>
🎵 TikTok: <a href="https://tiktok.com/@smartgoldsignals" style="color:#38bdf8">@smartgoldsignals</a>
"""

PAYMENTS = """
💳 Lipa Na Mpesa<br>
🏦 Paybill: <b>322372</b><br>
🔢 Account: <b>YOUR UNIQUE SIGN-UP CODE</b>
"""


# ================= HOME =================
@app.route("/")
def home():
    return render_template_string(f"""
    <html>
    <head>
    <style>
        body {{
            margin:0;
            font-family:Arial;
            background:{BG};
            color:white;
        }}

        .nav {{
            display:flex;
            justify-content:space-between;
            padding:15px;
            background:#0f172a;
            border-bottom:1px solid #1f2937;
        }}

        .logo {{
            font-size:20px;
            color:{ACCENT};
            font-weight:bold;
        }}

        .grid {{
            display:grid;
            grid-template-columns:repeat(2,1fr);
            gap:12px;
            padding:15px;
        }}

        .card {{
            background:{CARD};
            padding:20px;
            border-radius:12px;
            text-align:center;
            border:1px solid #1f2937;
        }}

        a {{
            color:{ACCENT};
            text-decoration:none;
            font-weight:bold;
        }}

        .section {{
            padding:15px;
            background:{CARD};
            margin:10px;
            border-radius:12px;
        }}
    </style>
    </head>

    <body>

    <div class="nav">
        <div class="logo">🚀 PESAMATRIX SIGNALS</div>
        <a href="/login">ADMIN</a>
    </div>

    <div class="grid">

        <div class="card"><a href="/videos">🎥 Free Videos</a></div>
        <div class="card"><a href="/news">📰 Trading News</a></div>
        <div class="card"><a href="/access">🔐 Premium Signals</a></div>
        <div class="card"><a href="/posts">📊 Latest Posts</a></div>
        <div class="card"><a href="/register">🟢 Join</a></div>
        <div class="card"><a href="/signals">📈 Signals</a></div>

    </div>

    <div class="section">
        <h3>About</h3>
        <p>We deliver high accuracy trading signals in real time.</p>
    </div>

    <div class="section">
        <h3>Contacts</h3>
        {CONTACTS}
    </div>

    <div class="section">
        <h3>Payments</h3>
        {PAYMENTS}
    </div>

    </body>
    </html>
    """)


# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        unique_code = str(uuid.uuid4())[:6].upper()

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                    (request.form["name"], request.form["contact"], datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"JOIN SUCCESS. YOUR ACCOUNT CODE: {unique_code}"

    return """
    <body style="background:#0b1220;color:white">
    <form method='post'>
        <input name='name' placeholder='Name'><br>
        <input name='contact' placeholder='Contact'><br>
        <button>Join</button>
    </form>
    </body>
    """


# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return "<body style='background:#0b1220;color:white'><form method='post'><input name='password'><button>Login</button></form></body>"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <h1 style="color:{ACCENT}">ADMIN DASHBOARD</h1>

    <h3>Settings</h3>
    <form method='post'>
        <input name='about' placeholder='About'><br>
        <input name='phone' placeholder='Phone'><br>
        <input name='email' placeholder='Email'><br>
        <input name='social' placeholder='Social'><br>
        <input name='bg' placeholder='Background'><br>
        <input name='font' placeholder='Font'><br>
        <button>Save</button>
    </form>

    <br>
    <a href="/generate_code">Generate Code</a><br>
    <a href="/codes">Saved Codes</a><br>
    <a href="/upload">Upload Media</a><br>
    <a href="/trade">Create Trade</a><br>

    </body>
    """


# ================= CODE GENERATOR =================
@app.route("/generate_code")
def generate_code():
    if not session.get("admin"):
        return redirect("/login")

    code = str(uuid.uuid4())[:8].upper()
    expiry = datetime.now() + timedelta(days=7)

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO access_codes VALUES (NULL,?,?)",
                (code, expiry.isoformat()))
    conn.commit()
    conn.close()

    return f"<body style='background:{BG};color:white'>CODE: {code}</body>"


# ================= SIGNALS (LOCKED) =================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h1>🔐 PREMIUM SIGNALS</h1>"

    for r in rows:
        out += f"""
        <div style='background:{CARD};margin:10px;padding:15px;border-radius:12px'>
            📊 Pair: {r['symbol']}<br>
            📥 Entry: {r['entry']}<br>
            🎯 TP: {r['tp']}<br>
            🛑 SL: {r['sl']}<br>
            📌 Status: {r['status']}
        </div>
        """

    return out + "</body>"


# ================= ACCESS =================
@app.route("/access", methods=["GET","POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        row = cur.fetchone()
        conn.close()

        if row:
            session["access"] = True
            return redirect("/signals")

        return "Invalid code"

    return "<body style='background:#0b1220;color:white'><form method='post'><input name='code'><button>Unlock</button></form></body>"


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
