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
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"

LOGO = "/static/logo.png"  # <-- SAVE YOUR IMAGE AS static/logo.png

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

    cur.execute("""CREATE TABLE IF NOT EXISTS access_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        expiry TEXT
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

# ================= HOME =================
@app.route("/")
def home():
    return f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <div style="text-align:center;padding:20px">
        <img src="{LOGO}" width="150"><br>
        <h2 style="color:{ACCENT}">PESAMATRIX</h2>
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
        <input name='name'><br>
        <input name='contact'><br>
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
    </body>
    """

# ================= ACCESS =================
@app.route("/access")
def access():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]

    if datetime.now() > datetime.fromisoformat(user["trial_end"]):
        return f"<body style='background:{BG};color:white'>Trial Expired</body>"

    return redirect("/signals")

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
        📊 {r['symbol']}<br>
        📥 Entry: {r['entry']}<br>
        🎯 TP: {r['tp']}<br>
        🛑 SL: {r['sl']}<br>
        📌 Status: {r['status']}
        </div>
        """
    return out

# ================= ADMIN LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

    return f"<body style='background:{BG};color:white'><form method='post'><input name='password'><button>Login</button></form></body>"

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return f"""
    <body style="background:{BG};color:white">
    <h1>ADMIN</h1>

    <a href="/generate_code">Generate Code</a><br>
    <a href="/users">Users</a><br>
    <a href="/create_trade">Create Signal</a><br>
    <a href="/manage_trades">Manage Trades</a><br>
    <a href="/upload">Upload Media</a><br>

    </body>
    """

# ================= CREATE TRADE =================
@app.route("/create_trade", methods=["GET","POST"])
def create_trade():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        conn = db()
        cur = conn.cursor()

        cur.execute("INSERT INTO trades VALUES (NULL,?,?,?,?,?,?,?,?)",
                    (request.form["symbol"],
                     request.form["side"],
                     float(request.form["entry"]),
                     float(request.form["sl"]),
                     float(request.form["tp"]),
                     "ACTIVE",
                     datetime.now().isoformat(),
                     (datetime.now()+timedelta(hours=4)).isoformat()))

        conn.commit()
        conn.close()
        return redirect("/admin")

    return f"""
    <body style="background:{BG};color:white">
    <h2>Create Signal</h2>
    <form method='post'>
    Pair:<br><input name='symbol'><br>
    Side:<br><input name='side'><br>
    Entry:<br><input name='entry'><br>
    SL:<br><input name='sl'><br>
    TP:<br><input name='tp'><br>
    <button>Create</button>
    </form>
    </body>
    """

# ================= MANAGE TRADES =================
@app.route("/manage_trades", methods=["GET","POST"])
def manage_trades():
    if not session.get("admin"):
        return redirect("/login")

    conn = db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("UPDATE trades SET status=? WHERE id=?",
                    (request.form["status"], request.form["id"]))
        conn.commit()

    cur.execute("SELECT * FROM trades")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h2>Manage Trades</h2>"
    for r in rows:
        out += f"""
        <div style='background:{CARD};margin:10px;padding:10px'>
        {r['symbol']} | {r['status']}
        <form method='post'>
        <input type='hidden' name='id' value='{r['id']}'>
        <select name='status'>
        <option>ACTIVE</option>
        <option>RUNNING</option>
        <option>EXPIRED</option>
        </select>
        <button>Update</button>
        </form>
        </div>
        """
    return out

# ================= UPLOAD =================
@app.route("/upload", methods=["GET","POST"])
def upload():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files.get("file")
        link = request.form.get("link")

        media_path = ""

        if file and file.filename:
            filename = secure_filename(file.filename)
            media_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(media_path)
        elif link:
            media_path = link

        media_type = "video" if ".mp4" in media_path else "image"

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO posts VALUES (NULL,?,?,?,?,?)",
                    (request.form["title"], request.form["content"], media_path, media_type, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return redirect("/admin")

    return f"""
    <body style="background:{BG};color:white">
    <h2>Upload Media</h2>
    <form method='post' enctype='multipart/form-data'>
    Title:<br><input name='title'><br>
    Content:<br><input name='content'><br>
    File:<br><input type='file' name='file'><br>
    OR Link:<br><input name='link'><br>
    <button>Upload</button>
    </form>
    </body>
    """

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
