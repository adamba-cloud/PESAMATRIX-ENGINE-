import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "super_secret_key_change_me"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)

# ================= STYLE =================
BG = "#0b1220"
CARD = "#111a2e"
BLUE = "#38bdf8"
WHITE = "white"

STYLE = f"""
font-family:Arial;
color:{WHITE};
background:{BG};
"""

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

    cur.execute("""CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY,
        title TEXT,
        content TEXT,
        media TEXT,
        type TEXT
    )""")

    conn.commit()
    conn.close()

init()

# ================= UI HELPERS =================
def header(text):
    return f"""
    <div style="background:{CARD};padding:20px;text-align:center">
        <h1 style="color:{BLUE}">{text}</h1>
    </div>
    """

def card(content):
    return f"""
    <div style="background:{CARD};padding:15px;margin:10px;border-radius:10px">
        {content}
    </div>
    """

def button(label, link):
    return f"<a href='{link}' style='color:{BLUE}'>{label}</a>"

# ================= LANDING PAGE (BUSY) =================
@app.route("/")
def home():
    return f"""
    <body style="{STYLE}">

    {header("🚀 PESAMATRIX TRADING PLATFORM")}

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:15px">

        {card("📊 Free Videos<br><a href='/videos' style='color:{BLUE}'>Open</a>")}
        {card("📰 Latest Posts<br><a href='/posts' style='color:{BLUE}'>Open</a>")}
        {card("📡 Trading News<br><a href='/news' style='color:{BLUE}'>Open</a>")}
        {card("🔐 Premium Signals (LOCKED)<br><a href='/premium' style='color:{BLUE}'>Access</a>")}
        {card("🟢 Register<br><a href='/register' style='color:{BLUE}'>Join</a>")}
        {card("👤 Login<br><a href='/login' style='color:{BLUE}'>Enter</a>")}

    </div>

    {card("<h3 style='color:"+BLUE+"'>ABOUT US</h3>We provide forex signals, risk management, and trading education.")}

    {card("""
        <h3 style='color:#38bdf8'>CONTACT</h3>
        📞 +254781585319<br>
        📞 +254717434943<br>
        🔗 TikTok: <a style='color:#38bdf8' href='https://tiktok.com/@smartgoldsignals'>@smartgoldsignals</a>
    """)}

    {card("""
        <h3 style='color:#38bdf8'>PAYMENT METHODS</h3>
        Mpesa Paybill: <b>322372</b><br>
        Account = Your Code after registration
    """)}

    </body>
    """

# ================= REGISTER =================
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

        return f"""
        <body style="{STYLE}">
        <h2 style="color:{BLUE}">Your Account Code</h2>
        <h1>{code}</h1>
        <a href='/login' style='color:{BLUE}'>Login</a>
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

# ================= LOGIN =================
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

# ================= DASHBOARD =================
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

    {card("<a href='/signals' style='color:#38bdf8'>View Signals</a>")}
    {card("<a href='/premium' style='color:#38bdf8'>Premium (Locked System)</a>")}

    </body>
    """

# ================= PREMIUM LOCK =================
@app.route("/premium")
def premium():
    if "user" not in session:
        return redirect("/login")

    u = session["user"]

    if datetime.now() > datetime.fromisoformat(u["trial_end"]):
        return f"<body style='{STYLE}'><h2 style='color:{BLUE}'>🔒 Locked - Please Pay</h2></body>"

    return redirect("/signals")

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('LIVE SIGNALS')}"

    for r in rows:
        out += card(f"""
        <b>{r['symbol']}</b><br>
        Entry: {r['entry']}<br>
        TP: {r['tp']}<br>
        SL: {r['sl']}<br>
        Status: {r['status']}
        """)

    return out + "</body>"

# ================= POSTS =================
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('LATEST POSTS')}"

    for r in rows:
        out += card(r["title"])

    return out + "</body>"

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('VIDEOS')}"

    for r in rows:
        out += f"<video controls width='100%'><source src='/{r['media']}'></video>"

    return out + "</body>"

# ================= NEWS =================
@app.route("/news")
def news():
    return f"<body style='{STYLE}'>{header('TRADING NEWS')}Coming Soon</body>"

# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")

    if not session.get("admin"):
        return """
        <form method="POST">
            Admin Password:<br>
            <input name="password">
            <button>Login</button>
        </form>
        """

    return f"""
    <body style="{STYLE}">
    {header("ADMIN PANEL")}

    <a href="/create_trade" style="color:{BLUE}">Create Trade</a><br>
    <a href="/users" style="color:{BLUE}">Users</a><br>

    </body>
    """

# ================= CREATE TRADE =================
@app.route("/create_trade", methods=["GET","POST"])
def create_trade():
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

    out = "<body style='background:#0b1220;color:white'><h2>Users</h2>"
    for u in rows:
        out += f"<div>{u['name']} | {u['code']}</div>"

    return out + "</body>"

# ================= MPESA CALLBACK =================
@app.route("/mpesa_callback", methods=["POST"])
def mpesa():
    print(request.json)
    return {"status": "ok"}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
