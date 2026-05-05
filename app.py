import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_RANDOM_SECRET"

# ================= CONFIG =================
ADMIN_PASSWORD = "admin123"
UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)

BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"
TEXT = "font-size:18px;font-family:Arial;"

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

# ================= UI =================
def header(title):
    return f"""
    <div style="padding:20px;background:{CARD};color:{ACCENT};text-align:center;font-size:24px">
        {title}
    </div>
    """

def card(content):
    return f"""
    <div style="background:{CARD};padding:15px;margin:10px;border-radius:12px">
        {content}
    </div>
    """

def footer(user=None):
    acc = user["account_code"] if user else "N/A"
    return f"""
    <div style="padding:15px;background:{CARD};margin-top:20px">
        <h3 style="color:{ACCENT}">📞 Contact</h3>
        +254781585319 | +254717434943<br><br>

        <a style="color:{ACCENT}" href="https://tiktok.com/@smartgoldsignals">TikTok</a><br><br>

        <h3 style="color:{ACCENT}">💳 Payments</h3>
        Mpesa Paybill: <b>322372</b><br>
        Account: <b>{acc}</b>
    </div>
    """

# ================= HOME =================
@app.route("/")
def home():
    return f"""
    <body style="background:{BG};color:white;{TEXT}">

    {header("🚀 PESAMATRIX TRADING")}

    <div style="padding:15px;display:grid;grid-template-columns:1fr 1fr;gap:10px">

        {card('<a href="/register" style="color:#38bdf8">🟢 Join Now</a>')}
        {card('<a href="/login" style="color:#38bdf8">👤 User Login</a>')}
        {card('<a href="/admin" style="color:#38bdf8">⚙ Admin Panel</a>')}
        {card('<a href="/signals" style="color:#38bdf8">📊 Live Signals</a>')}
        {card('<a href="/videos" style="color:#38bdf8">🎥 Videos</a>')}
        {card('<a href="/news" style="color:#38bdf8">📰 News</a>')}

    </div>

    {card("<h3>About Us</h3>We provide high accuracy forex signals, risk management, and trading education.")}

    {footer()}

    </body>
    """

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()
        trial_end = datetime.now() + timedelta(days=3)

        conn = db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO users VALUES (NULL,?,?,?,?,?)""",
                    (request.form["name"], request.form["contact"], code,
                     trial_end.isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"""
        <body style="background:{BG};color:white">
        <h2>Your Account Code</h2>
        <h1 style="color:{ACCENT}">{code}</h1>
        <a href="/login">Login</a>
        </body>
        """

    return f"""
    <body style="background:{BG};color:white;{TEXT}">
    <h2>Register</h2>

    <form method="POST">
        Name:<br><input name="name"><br><br>
        Phone:<br><input name="contact"><br><br>
        <button>Register</button>
    </form>

    </body>
    """

# ================= USER LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE account_code=?", (request.form["code"],))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)
            return redirect("/dashboard")

    return """
    <body style="background:#0b1220;color:white">
    <form method="POST">
        Enter Code:<br>
        <input name="code"><br><br>
        <button>Login</button>
    </form>
    </body>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    status = "ACTIVE" if datetime.now() < datetime.fromisoformat(user["trial_end"]) else "EXPIRED"

    return f"""
    <body style="background:{BG};color:white;{TEXT}">

    {header("USER DASHBOARD")}

    {card(f"Name: {user['name']}<br>Account: {user['account_code']}<br>Status: {status}")}

    <a href="/signals" style="color:{ACCENT}">View Signals</a><br>
    <a href="/logout" style="color:red">Logout</a>

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

    out = f"<body style='background:{BG};color:white'>"
    out += header("LIVE SIGNALS")

    for r in rows:
        out += card(f"""
        <b>{r['symbol']}</b><br>
        Entry: {r['entry']}<br>
        TP: {r['tp']}<br>
        SL: {r['sl']}<br>
        Status: {r['status']}
        """)

    return out + "</body>"

# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

    if not session.get("admin"):
        return """
        <body style="background:#0b1220;color:white">
        <form method="POST">
            Admin Password:<br>
            <input name="password"><br><br>
            <button>Login</button>
        </form>
        </body>
        """

    return """
    <body style="background:#0b1220;color:white">

    <h2>ADMIN PANEL</h2>

    <a href="/create_trade">Create Trade</a><br>
    <a href="/manage">Manage Trades</a><br>
    <a href="/upload">Upload Video</a><br>
    <a href="/users">Users</a><br>

    </body>
    """

# ================= CREATE TRADE =================
@app.route("/create_trade", methods=["GET","POST"])
def create_trade():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO trades VALUES (NULL,?,?,?,?)",
                    (request.form["symbol"],
                     request.form["entry"],
                     request.form["sl"],
                     request.form["tp"],
                     request.form["status"]))
        conn.commit()
        conn.close()
        return redirect("/admin")

    return """
    <form method="POST">
        Symbol:<input name="symbol"><br>
        Entry:<input name="entry"><br>
        SL:<input name="sl"><br>
        TP:<input name="tp"><br>
        Status:<input name="status"><br>
        <button>Create</button>
    </form>
    """

# ================= USERS =================
@app.route("/users")
def users():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'>"
    out += "<h2>Users</h2>"

    for u in rows:
        out += f"<div>{u['name']} | {u['account_code']}</div>"

    return out + "</body>"

# ================= VIDEO UPLOAD =================
@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO posts VALUES (NULL,?,?,?,?)",
                    ("Video", "", path, "video"))
        conn.commit()
        conn.close()

        return redirect("/admin")

    return """
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file">
        <button>Upload</button>
    </form>
    """

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = "<body style='background:#0b1220;color:white'>"
    out += header("VIDEOS")

    for r in rows:
        out += f"<video controls width='100%'><source src='/{r['media']}'></video>"

    return out + "</body>"

# ================= NEWS =================
@app.route("/news")
def news():
    return f"<body style='background:{BG};color:white'>{header('NEWS')} Coming soon</body>"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= MPESA CALLBACK (READY) =================
@app.route("/mpesa_callback", methods=["POST"])
def mpesa_callback():
    data = request.json
    print("MPESA:", data)
    return {"status": "received"}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
