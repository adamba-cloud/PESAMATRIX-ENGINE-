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

# ================= REGISTER =================
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
    <form method='post'>
    Name:<br><input name='name'><br><br>
    Phone Number:<br><input name='phone'><br><br>
    <button>Join</button>
    </form>
    </body>
    """

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

    return f"<body style='background:{BG};color:white;{TEXT}'><form method='post'>Account Code:<br><input name='code'><button>Login</button></form></body>"

# ================= DASHBOARD =================
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

    out = f"<body style='background:{BG};color:white;{TEXT}'><h2 style='color:{ACCENT}'>Live Signals</h2>"

    for r in rows:
        out += f"""
        <div style='background:{CARD};margin:10px;padding:15px;border-radius:10px'>
        <b style='color:{ACCENT}'>{r['symbol']}</b><br><br>
        Entry Point: {r['entry']}<br>
        Take Profit (TP): {r['tp']}<br>
        Stop Loss (SL): {r['sl']}<br>
        Status: <b>{r['status']}</b>
        </div>
        """
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

# ================= CREATE TRADE =================
@app.route("/create_trade", methods=["GET","POST"])
def create_trade():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO trades VALUES (NULL,?,?,?,?,?,?,?,?)",
                    (request.form["pair"],
                     "BUY",
                     request.form["entry"],
                     request.form["sl"],
                     request.form["tp"],
                     "ACTIVE",
                     datetime.now(),
                     datetime.now()))
        conn.commit()
        conn.close()
        return redirect("/admin")

    return f"""
    <body style="background:{BG};color:white;{TEXT}">
    Pair:<br><input name='pair'><br>
    Entry Point:<br><input name='entry'><br>
    Take Profit (TP):<br><input name='tp'><br>
    Stop Loss (SL):<br><input name='sl'><br>
    <button>Create</button>
    </body>
    """

# ================= OTHER ROUTES =================
@app.route("/manage_trades")
def manage_trades():
    return "<h2>Manage Trades Working</h2>"

@app.route("/upload", methods=["GET","POST"])
def upload():
    return "<h2>Upload Page Working</h2>"

@app.route("/generate_code")
def generate_code():
    return "<h2>Code Generated</h2>"

@app.route("/users")
def users():
    return "<h2>Users List</h2>"

@app.route("/create_news")
def create_news():
    return "<h2>Create News Page</h2>"

# ================= START =================
if __name__ == "__main__":
    app.run()
