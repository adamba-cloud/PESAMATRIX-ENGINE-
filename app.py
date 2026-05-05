import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, send_from_directory

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET"

# ================= FOLDERS =================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)

# ================= UI THEME (STRIPE STYLE) =================
BG = "#0b1220"
CARD = "#111a2e"
BLUE = "#38bdf8"
TEXT = "white"

STYLE = f"""
margin:0;
font-family:Arial;
background:{BG};
color:{TEXT};
"""

# ================= DATABASE =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        code TEXT,
        role TEXT,
        trial_end TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        entry TEXT,
        sl TEXT,
        tp TEXT,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS media(
        id INTEGER PRIMARY KEY,
        filename TEXT,
        type TEXT
    )""")

    conn.commit()
    conn.close()

init()

# ================= UI COMPONENTS =================
def header(title):
    return f"""
    <div style="background:{CARD};padding:25px;text-align:center">
        <h1 style="color:{BLUE};margin:0">PESAMATRIX</h1>
        <h3 style="margin:5px">{title}</h3>
    </div>
    """

def card(content):
    return f"""
    <div style="background:{CARD};padding:15px;margin:10px;border-radius:12px">
        {content}
    </div>
    """

def btn(text, link):
    return f"""
    <a href="{link}" 
       style="background:{BLUE};color:black;padding:10px 15px;
       border-radius:8px;text-decoration:none;font-weight:bold">
       {text}
    </a>
    """

# =====================================================
# 🟦 LANDING PAGE (SAAS STYLE)
# =====================================================
@app.route("/")
def home():
    return f"""
    <body style="{STYLE}">

    {header("Smart Trading SaaS Platform")}

    <div style="padding:20px;text-align:center">
        <h2 style="color:{BLUE}">Trade Smarter. Scale Faster.</h2>
        <p>Signals • Analytics • Automation • Trading Intelligence</p>

        <br>
        {btn("🔐 Admin Dashboard", "/admin")}
        &nbsp;
        {btn("Create Account", "/register")}
    </div>

    {card("""
        <h3 style='color:#38bdf8'>ABOUT US</h3>
        We provide premium forex signals, market analysis,
        and automated trading tools for serious traders.
    """)}

    {card("""
        <h3 style='color:#38bdf8'>CONTACT</h3>
        📞 <a href='tel:+254781585319' style='color:#38bdf8'>Call Support</a><br>
        📞 <a href='tel:+254717434943' style='color:#38bdf8'>WhatsApp</a><br>
        🎵 <a href='https://tiktok.com/@smartgoldsignals' style='color:#38bdf8'>TikTok</a>
    """)}

    {card("""
        <h3 style='color:#38bdf8'>PAYMENTS</h3>
        Mpesa Paybill: <b>322372</b><br>
        Account: Your user code
    """)}

    </body>
    """

# =====================================================
# 🟩 USER SYSTEM
# =====================================================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()
        trial = datetime.now() + timedelta(days=3)

        conn = db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO users 
        VALUES(NULL,?,?,?,?,?,?)""",
        (request.form["name"],
         request.form["phone"],
         code,
         "user",
         trial.isoformat(),
         datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"""
        <body style="{STYLE}">
        {header("ACCOUNT CREATED")}
        <h2>Your Code: {code}</h2>
        <a href="/login" style="color:{BLUE}">Login</a>
        </body>
        """

    return f"""
    <body style="{STYLE}">
    {header("REGISTER")}
    <form method="POST">
        Name:<br><input name="name"><br><br>
        Phone:<br><input name="phone"><br><br>
        <button>Register</button>
    </form>
    </body>
    """

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE code=?", (request.form["code"],))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)
            return redirect("/dashboard")

    return f"""
    <body style="{STYLE}">
    {header("LOGIN")}
    <form method="POST">
        Code:<br><input name="code"><br><br>
        <button>Login</button>
    </form>
    </body>
    """

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    u = session["user"]
    status = "ACTIVE" if datetime.now() < datetime.fromisoformat(u["trial_end"]) else "EXPIRED"

    return f"""
    <body style="{STYLE}">
    {header("USER DASHBOARD")}

    {card(f"Name: {u['name']}<br>Code: {u['code']}<br>Status: {status}")}

    {card(btn("View Signals","/signals"))}
    {card(btn("Media Gallery","/media"))}

    </body>
    """

# =====================================================
# 🟥 ADMIN SYSTEM (ROLE BASED)
# =====================================================
def is_admin():
    return session.get("role") == "admin"

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            session["role"] = "admin"
            return redirect("/admin")

    if not is_admin():
        return f"""
        <body style="{STYLE}">
        {header("ADMIN LOGIN")}
        <form method="POST">
            Password:<br><input name="password"><br><br>
            <button>Login</button>
        </form>
        </body>
        """

    conn = db()
    cur = conn.cursor()
    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trades = cur.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    media = cur.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    conn.close()

    return f"""
    <body style="{STYLE}">
    {header("ADMIN DASHBOARD")}

    {card(f"Users: {users} | Trades: {trades} | Media: {media}")}

    {card(btn("📊 Create Trade","/admin/trades"))}
    {card(btn("🎥 Upload Media","/admin/media"))}
    {card(btn("👥 Users","/admin/users"))}

    </body>
    """

# =====================================================
# 🟧 ADMIN MEDIA UPLOAD PANEL
# =====================================================
@app.route("/admin/media", methods=["GET","POST"])
def upload_media():
    if not is_admin():
        return redirect("/admin")

    if request.method == "POST":
        file = request.files["file"]
        if file:
            filename = file.filename
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            conn = db()
            cur = conn.cursor()
            cur.execute("INSERT INTO media VALUES(NULL,?,?)",
                        (filename, "image"))
            conn.commit()
            conn.close()

    return f"""
    <body style="{STYLE}">
    {header("MEDIA UPLOAD (ADMIN ONLY)")}

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <button>Upload</button>
    </form>

    <br>
    <a href="/media" style="color:{BLUE}">View Gallery</a>
    </body>
    """

@app.route("/media")
def media():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM media").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('MEDIA GALLERY')}"

    for m in rows:
        out += card(f"<img src='/static/uploads/{m['filename']}' width='100%'>")

    return out + "</body>"

# =====================================================
# 🟨 TRADE SYSTEM (ADMIN ONLY)
# =====================================================
@app.route("/admin/trades", methods=["GET","POST"])
def create_trade():
    if not is_admin():
        return redirect("/admin")

    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO trades VALUES(NULL,?,?,?,?,?)",
        (request.form["symbol"],
         request.form["entry"],
         request.form["sl"],
         request.form["tp"],
         request.form["status"]))
        conn.commit()
        conn.close()
        return redirect("/admin")

    return f"""
    <body style="{STYLE}">
    {header("CREATE TRADE")}

    <form method="POST">
        Symbol:<input name="symbol"><br>
        Entry:<input name="entry"><br>
        SL:<input name="sl"><br>
        TP:<input name="tp"><br>
        Status:<input name="status"><br><br>
        <button>Create</button>
    </form>
    </body>
    """

# =====================================================
# 🟩 SIGNALS (USER VIEW)
# =====================================================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('LIVE SIGNALS')}"

    for r in rows:
        out += card(f"{r['symbol']} | {r['entry']} | {r['tp']} | {r['sl']} | {r['status']}")

    return out + "</body>"

# =====================================================
# RUN APP
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
