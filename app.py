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

BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"

CONTACTS = """
📞 <a href="tel:+254781585319" style="color:#38bdf8">+254 781 585 319</a><br>
📞 <a href="tel:+254717434943" style="color:#38bdf8">+254 717 434 943</a><br>
📧 support@pesamatrix.com<br>
🎵 TikTok: <a href="https://tiktok.com/@smartgoldsignals" style="color:#38bdf8">@smartgoldsignals</a>
"""

PAYMENTS = """
💳 Lipa Na Mpesa<br>
🏦 Paybill: <b>322372</b><br>
🔢 Account: <b>Your Unique Join Code</b>
"""

# ================= DATABASE =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT,
        account_code TEXT,
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

    cur.execute("""CREATE TABLE IF NOT EXISTS access_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        expiry TEXT
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
        }}
        .grid {{
            display:grid;
            grid-template-columns:repeat(2,1fr);
            gap:12px;
            padding:15px;
        }}
        .card {{
            background:{CARD};
            padding:18px;
            border-radius:12px;
            text-align:center;
        }}
        a {{
            color:{ACCENT};
            text-decoration:none;
            font-weight:bold;
        }}
        .section {{
            margin:10px;
            padding:15px;
            background:{CARD};
            border-radius:12px;
        }}
    </style>
    </head>

    <body>

    <div class="nav">
        <h2 style="color:{ACCENT}">🚀 PESAMATRIX</h2>
        <a href="/login">Admin</a>
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
        code = str(uuid.uuid4())[:8].upper()

        conn = db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO users VALUES (NULL,?,?,?,?)
        """, (
            request.form["name"],
            request.form["contact"],
            code,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        return f"""
        <body style="background:{BG};color:white">
        <h2>JOIN SUCCESS</h2>
        <p>Your Account Number:</p>
        <h1 style="color:{ACCENT}">{code}</h1>
        <a href="/">Go Home</a>
        </body>
        """

    return f"""
    <body style="background:{BG};color:white">
    <form method='post'>
        <input name='name' placeholder='Name'><br><br>
        <input name='contact' placeholder='Contact'><br><br>
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
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return f"""
    <body style="background:{BG};color:white">
    <h1 style="color:{ACCENT}">ADMIN DASHBOARD</h1>

    <a href="/generate_code">Generate Code</a><br>
    <a href="/codes">Saved Codes</a><br>
    <a href="/upload">Upload</a><br>
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
    cur.execute("INSERT INTO access_codes VALUES (NULL,?,?)", (code, expiry.isoformat()))
    conn.commit()
    conn.close()

    return f"<body style='background:{BG};color:white'>CODE: {code}</body>"

@app.route("/codes")
def codes():
    if not session.get("admin"):
        return redirect("/login")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM access_codes ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'><h1>CODES</h1>"
    for r in rows:
        out += f"<div>{r['code']} | {r['expiry']}</div>"
    return out + "</body>"

# ================= UPLOAD =================
@app.route("/upload", methods=["GET","POST"])
def upload():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        media_type = "image"
        if filename.endswith(("mp4","mov")):
            media_type = "video"

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO posts VALUES (NULL,?,?,?,?,?)",
                    (request.form["title"], request.form["content"], path, media_type, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return redirect("/admin")

    return "<body style='background:#0b1220;color:white'><form method='post' enctype='multipart/form-data'><input name='title'><input name='content'><input type='file' name='file'><button>Upload</button></form></body>"

# ================= TRADE =================
@app.route("/trade", methods=["GET","POST"])
def trade():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO trades VALUES (NULL,?,?,?,?,?,?,?,?)",
                    (request.form["symbol"], request.form["side"],
                     float(request.form["entry"]), float(request.form["sl"]),
                     float(request.form["tp"]), "ACTIVE",
                     datetime.now().isoformat(),
                     (datetime.now()+timedelta(hours=4)).isoformat()))
        conn.commit()
        conn.close()
        return redirect("/admin")

    return "<body style='background:#0b1220;color:white'><form method='post'><input name='symbol'><input name='side'><input name='entry'><input name='sl'><input name='tp'><button>Create</button></form></body>"

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

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'><h1>🔐 SIGNALS</h1>"

    for r in rows:
        out += f"""
        <div style='background:#111a2e;margin:10px;padding:15px;border-radius:12px'>
            📊 {r['symbol']}<br>
            📥 Entry: {r['entry']}<br>
            🎯 TP: {r['tp']}<br>
            🛑 SL: {r['sl']}<br>
        </div>
        """

    return out + "</body>"

# ================= NEWS =================
@app.route("/news")
def news():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'><h1>NEWS</h1>"
    for r in rows:
        out += f"<div style='background:#111a2e;margin:10px;padding:10px'>{r['title']}</div>"
    return out + "</body>"

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'><h1>VIDEOS</h1>"
    for r in rows:
        out += f"<video controls width='100%'><source src='/{r['media']}'></video>"
    return out + "</body>"

# ================= POSTS =================
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'><h1>POSTS</h1>"
    for r in rows:
        out += f"<div style='background:#111a2e;margin:10px;padding:10px'>{r['title']}</div>"
    return out + "</body>"

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
