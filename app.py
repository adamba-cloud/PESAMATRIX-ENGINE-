import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_SECURE_SECRET"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)

# ================= BRANDING =================
BRAND = "PESAMATRIX"
TAGLINE = "Smart Forex Trading Platform"

BG = "#0b1220"
CARD = "#111a2e"
BLUE = "#38bdf8"
WHITE = "white"

STYLE = f"""
margin:0;
font-family:Arial;
background:{BG};
color:{WHITE};
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

# ================= UI SYSTEM =================
def header(title):
    return f"""
    <div style="background:{CARD};padding:25px;text-align:center">
        <h1 style="color:{BLUE};margin:0">{BRAND}</h1>
        <p style="color:#cbd5e1;margin:5px">{TAGLINE}</p>
        <h2 style="color:white">{title}</h2>
    </div>
    """

def card(content):
    return f"""
    <div style="background:{CARD};padding:15px;margin:10px;border-radius:12px">
        {content}
    </div>
    """

def btn(text, link):
    return f"<a href='{link}' style='color:{BLUE};text-decoration:none'>{text}</a>"

# ================= LANDING PAGE (SAAS BUSY UI) =================
@app.route("/")
def home():
    return f"""
    <body style="{STYLE}">

    {header("🚀 TRADE SMART. GROW FAST.")}

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:20px">

        {card("📊 Free Videos<br>{btn('Open','/videos')}")}
        {card("📰 Latest Posts<br>{btn('Open','/posts')}")}
        {card("📡 Trading News<br>{btn('Open','/news')}")}
        {card("🔐 Premium Signals (LOCKED)<br>{btn('Access','/premium')}")}
        {card("🟢 Register<br>{btn('Join','/register')}")}
        {card("👤 Login<br>{btn('Enter','/login')}")}

    </div>

    {card("""
        <h3 style='color:#38bdf8'>ABOUT US</h3>
        We provide professional forex signals, risk management systems and trading insights.
    """)}

    {card("""
        <h3 style='color:#38bdf8'>CONTACT</h3>
        📞 +254781585319<br>
        📞 +254717434943<br>
        🔗 TikTok: <a style='color:#38bdf8' href='https://tiktok.com/@smartgoldsignals'>@smartgoldsignals</a>
    """)}

    {card("""
        <h3 style='color:#38bdf8'>PAYMENT</h3>
        Mpesa Paybill: <b>322372</b><br>
        Account = Your Registration Code
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
        {header("ACCOUNT CREATED")}
        <h1 style="color:{BLUE}">{code}</h1>
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

    {card(btn("📊 View Signals","/signals"))}
    {card(btn("🔐 Premium Access","/premium"))}

    </body>
    """

# ================= PREMIUM LOCK =================
@app.route("/premium")
def premium():
    if "user" not in session:
        return redirect("/login")

    u = session["user"]

    if datetime.now() > datetime.fromisoformat(u["trial_end"]):
        return f"<body style='{STYLE}'>{header('LOCKED - PAYMENT REQUIRED')}</body>"

    return redirect("/signals")

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('LIVE SIGNALS')}"

    for r in rows:
        out += card(f"""
        <b style='color:{BLUE}'>{r['symbol']}</b><br>
        Entry: {r['entry']}<br>
        TP: {r['tp']}<br>
        SL: {r['sl']}<br>
        Status: {r['status']}
        """)

    return out + "</body>"

# ================= ADMIN DASHBOARD =================
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
            <input name="password">
            <button>Login</button>
        </form>
        </body>
        """

    conn = db()
    cur = conn.cursor()

    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trades = cur.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    posts = cur.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

    conn.close()

    return f"""
    <body style="{STYLE}">
    {header("ADMIN DASHBOARD")}

    {card(f"Users: {users} | Trades: {trades} | Posts: {posts}")}

    {card(btn("➕ Create Trade","/create_trade"))}
    {card(btn("🧑 Users","/users"))}
    {card(btn("📡 Manage Trades","/manage"))}

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

# ================= USERS =================
@app.route("/users")
def users():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM users").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('USERS')}"

    for u in rows:
        out += card(f"{u['name']} | {u['code']}")

    return out + "</body>"

# ================= MPESA CALLBACK =================
@app.route("/mpesa_callback", methods=["POST"])
def mpesa():
    print(request.json)
    return {"status": "ok"}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
