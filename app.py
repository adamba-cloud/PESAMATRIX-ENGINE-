import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

# ================= BRANDING =================
BRAND = "PESAMATRIX"
BG = "#0b1220"
CARD = "#111a2e"
BLUE = "#38bdf8"
WHITE = "white"

STYLE = f"font-family:Arial;background:{BG};color:{WHITE};margin:0"

# ================= DB =================
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

    conn.commit()
    conn.close()

init()

# ================= UI =================
def header(title):
    return f"""
    <div style="background:{CARD};padding:20px;text-align:center">
        <h1 style="color:{BLUE}">{BRAND}</h1>
        <h2>{title}</h2>
    </div>
    """

def box(content):
    return f"<div style='background:{CARD};padding:15px;margin:10px;border-radius:10px'>{content}</div>"

# =========================================================
# 🟦 LANDING SYSTEM (PUBLIC)
# =========================================================

@app.route("/")
def home():
    return f"""
    <body style="{STYLE}">
    {header("SMART FOREX TRADING PLATFORM")}

    {box("📊 <a href='/videos' style='color:{BLUE}'>Free Videos</a>")}
    {box("📰 <a href='/posts' style='color:{BLUE}'>Latest Posts</a>")}
    {box("📡 <a href='/news' style='color:{BLUE}'>Trading News</a>")}
    {box("🔐 <a href='/premium' style='color:{BLUE}'>Premium Signals (LOCKED)</a>")}
    {box("🟢 <a href='/register' style='color:{BLUE}'>Register</a>")}
    {box("👤 <a href='/login' style='color:{BLUE}'>Login</a>")}

    {box("ABOUT US: Professional forex signals and market analysis system.")}

    {box("CONTACT: +254781585319 | TikTok @smartgoldsignals")}

    </body>
    """

@app.route("/videos")
def videos():
    return f"<body style='{STYLE}'>{header('VIDEOS')}Coming Soon</body>"

@app.route("/posts")
def posts():
    return f"<body style='{STYLE}'>{header('POSTS')}Coming Soon</body>"

@app.route("/news")
def news():
    return f"<body style='{STYLE}'>{header('NEWS')}Coming Soon</body>"

# =========================================================
# 🟩 USER SYSTEM (AUTH + DASHBOARD)
# =========================================================

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()
        trial = datetime.now() + timedelta(days=3)

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                    (request.form["name"],
                     request.form["phone"],
                     code,
                     trial.isoformat(),
                     datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"<body style='{STYLE}'>{header('ACCOUNT CREATED')}CODE: {code}</body>"

    return f"""
    <body style="{STYLE}">
    {header("REGISTER")}
    <form method="POST">
        Name:<input name="name"><br><br>
        Phone:<input name="phone"><br><br>
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
        Code:<input name="code"><br><br>
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

    {box(f"Name: {u['name']}<br>Code: {u['code']}<br>Status: {status}")}

    {box("<a href='/signals' style='color:#38bdf8'>Signals</a>")}
    {box("<a href='/premium' style='color:#38bdf8'>Premium (LOCKED)</a>")}

    </body>
    """

@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('LIVE SIGNALS')}"

    for r in rows:
        out += box(f"{r['symbol']} | Entry {r['entry']} | TP {r['tp']} | SL {r['sl']} | {r['status']}")

    return out + "</body>"

@app.route("/premium")
def premium():
    if "user" not in session:
        return redirect("/login")

    u = session["user"]

    if datetime.now() > datetime.fromisoformat(u["trial_end"]):
        return f"<body style='{STYLE}'>{header('LOCKED - PAY TO ACCESS')}</body>"

    return redirect("/signals")

# =========================================================
# 🟥 ADMIN SYSTEM (CONTROL CENTER)
# =========================================================

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")

    if not session.get("admin"):
        return f"""
        <body style="{STYLE}">
        {header("ADMIN LOGIN")}
        <form method="POST">
            Password:<input name="password"><br><br>
            <button>Login</button>
        </form>
        </body>
        """

    conn = db()
    cur = conn.cursor()

    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trades = cur.execute("SELECT COUNT(*) FROM trades").fetchone()[0]

    conn.close()

    return f"""
    <body style="{STYLE}">
    {header("ADMIN DASHBOARD")}

    {box(f"Users: {users} | Trades: {trades}")}

    {box("<a href='/admin/trades' style='color:#38bdf8'>Manage Trades</a>")}
    {box("<a href='/admin/users' style='color:#38bdf8'>Users</a>")}
    {box("<a href='/admin/create_trade' style='color:#38bdf8'>Create Trade</a>")}

    </body>
    """

@app.route("/admin/create_trade", methods=["GET","POST"])
def create_trade():
    if not session.get("admin"):
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
        Status:<input name="status"><br>
        <button>Create</button>
    </form>
    </body>
    """

@app.route("/admin/users")
def admin_users():
    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM users").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('USERS')}"

    for u in rows:
        out += box(f"{u['name']} | {u['code']}")

    return out + "</body>"

# =========================================================
# MPESA CALLBACK
# =========================================================

@app.route("/mpesa_callback", methods=["POST"])
def mpesa():
    print(request.json)
    return {"status": "ok"}

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
